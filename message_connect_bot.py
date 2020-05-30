import logging
import yaml

from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters

from database_connection import DBConnection

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='info.log'
)

logger = logging.getLogger(__name__)

# states
ADDINGNAME, ADDINGPASS, CONFIRMATION = range(3)


# functions blog
def get_credentials_and_configurations():
    with open("config/credentials_and_configurations.yaml", 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.exception(exc)


def start(update, context):
    reply_text = "Hello! I am here to help you to setup hangouts connection and add account that you wish. "
    if context.user_data:
        reply_text += "You already told me account info: {} of your account you want to add. ".format(
            ", ".join(context.user_data.keys())
        )
        reply_text += "If you want to cancel adding this info, type cancel."
    else:
        reply_text += "Firstly, tell me account name you want to add"
    update.message.reply_text(reply_text)

    return ADDINGNAME


def add_new_account(update, context):
    update.message.reply_text("Firstly, tell me account name you want to add")

    return ADDINGNAME


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def add_account_name(update, context):
    name = update.message.text
    context.user_data['name_of_account'] = name
    update.message.reply_text('Thank you. Now give me a token of an account.')
    return ADDINGPASS


def add_account_token(update, context):
    token = update.message.text
    context.user_data['token_of_account'] = token
    update.message.reply_text(
        "Done! Now, check your data of the account and confirm adding. Type 'Yes' if you agree or anything if you don't"
    )
    return CONFIRMATION


def decorate_confirmation(function, db_handler):
    def wrapper(**kwargs):
        decision = function(**kwargs)
        if decision and add_account_to_db(
                db_handler,
                context.user_data['name_of_account'],
                context.user_data['token_of_account']
        ):
            update.message.reply_text(
                "Account was added"
            )
        else:
            if 'name_of_account' in context.user_data:
                del context.user_data['name_of_account']
            if 'token_of_account' in context.user_data:
                del context.user_data['token_of_account']
            update.message.reply_text(
                "Information typed previously was deleted. call /add_new_account to try again."
            )

            return ConversationHandler.END
        return wrapper


def do_confirmation(update, context):
    confirmation = update.message.text
    if confirmation.lower() == 'yes':
        return True
    else:
        return False


def add_account_to_db(dbms_handler, name, token):
    return dbms_handler.add_account(name, token)


def cancel(update, context):
    logger.info("Conversation was cancelled")
    update.message.reply_text('Bye!')

    return ConversationHandler.END


# Main logic
def main():
    # Getting credentails and configurations from config file
    creds_and_params = get_credentials_and_configurations()

    # Init database
    dbms_handler = DBConnection(creds_and_params, logger)

    updater = Updater(creds_and_params['bot_token'], use_context=True)

    # Adding handler
    dp = updater.dispatcher
    dp.add_error_handler(error)

    # decorating do_confirmation with init db
    do_confirmation = decorate_confirmation(do_confirmation, db_handler= dbms_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler("add_new_account", add_new_account)],
        states={
            ADDINGNAME: [MessageHandler(Filters.text, add_account_name)],
            ADDINGPASS: [MessageHandler(Filters.text, add_account_token)],
            CONFIRMATION: [MessageHandler(Filters.text, do_confirmation)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler('cancel', cancel))

    # Start the Bot
    updater.start_polling(poll_interval=5)
    updater.idle()


if __name__ == '__main__':
    main()
