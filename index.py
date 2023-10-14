import mysql.connector
import telebot
from telebot import types

# telegram config
bot = telebot.TeleBot("6632344856:AAEqNQEzc9sZ9XSVesjdTHkZPksX3t-5osY")

# database config
db = mysql.connector.connect(
    host="localhost", user="root", password="", database="todos")
mycur = db.cursor()


def setup_db():
    mycur.execute("CREATE TABLE IF NOT EXISTS `users`(\
            `user_id` int(30) PRIMARY KEY\
        );")

    mycur.execute("CREATE TABLE IF NOT EXISTS `tbl_todos` (\
            `todo_id` int(20) PRIMARY KEY AUTO_INCREMENT,\
            `user_id` int(30),\
            `description` varchar(200),\
            `completed` BOOLEAN,\
            FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`)\
        );")


def add_user(user_id):
    mycur.execute(
        f"INSERT INTO users VALUES ({user_id});")
    db.commit()


def add_todo(user_id, description):
    mycur.execute(
        f"INSERT INTO `tbl_todos`(`user_id`, `description`, `completed`) VALUES ('{user_id}','{description}','0')")
    db.commit()


def find_user(user_id):
    mycur.execute(f"SELECT * FROM `users` WHERE `user_id`={user_id};")
    return len(mycur.fetchall())


def delete_todo(todo_id):
    mycur.execute(f"DELETE FROM `tbl_todos` WHERE `todo_id`={todo_id};")
    db.commit()


def mark_complete(todo_id):
    mycur.execute(
        f"UPDATE `tbl_todos` SET `completed`=1 WHERE `todo_id`={todo_id};")
    db.commit()


def get_todos(user_id):
    mycur.execute(
        f"SELECT `todo_id`, `description`, `completed` FROM `tbl_todos` WHERE `user_id`={user_id};")
    res = mycur.fetchall()
    db.commit()
    return res


@ bot.message_handler(commands=['start'])
def send_welcome(message):
    if (find_user(int(message.chat.id)) == 0):
        add_user(int(message.chat.id))

    bot.send_message(int(message.chat.id),
                     f"Hello, {message.chat.first_name} \n")
    bot.reply_to(
        message, "Welcome to the Todo Bot!\n/add <task> to add a task,\n /list to list tasks,\n /delete <task_id> to delete.")


@ bot.message_handler(commands=['add'])
def add_todo_cmd(message):
    parts = message.text.split(' ', 1)
    if len(parts) == 1:
        bot.reply_to(
            message, "Please provide a task description. Use: /add <your_task>")
        return

    todo = parts[1]
    add_todo(int(message.chat.id), todo)
    bot.reply_to(message, f"Todo '{todo}' added!")


@ bot.message_handler(commands=['list'])
def list_todo_cmd(message):
    todos = get_todos(int(message.chat.id))
    # print("todos---lsit", message.chat.first_name)
    if not todos:
        bot.send_message(int(message.chat.id), "You Have No Todos.")
        return

    for todo in todos:
        todo_id, description, completed = todo
        status = "✅" if completed else "❌"

        markup = types.InlineKeyboardMarkup()
        button_text = "Mark as Done" if not completed else "Already done"
        callback_data = f"done_{todo_id}" if not completed else "noop"
        markup.add(types.InlineKeyboardButton(
            text=button_text, callback_data=callback_data))

        bot.send_message(
            message.chat.id, f"{todo_id}.{status}{description}", reply_markup=markup)


@ bot.callback_query_handler(func=lambda call: call.data.startswith('done_'))
def callback_markdone(call):
    todo_id = int(call.data.split("_")[1])
    mark_complete(todo_id)
    bot.answer_callback_query(call.id, "Task marked as done!")
    bot.edit_message_text("✅ Task completed!",
                          call.message.chat.id, call.message.message_id)


@ bot.message_handler(commands=['delete'])
def delete_task_cmd(message):
    llen = len(message.text.split(' ', 1))
    if llen == 2:
        todo_id = int(message.text.split(' ', 1)[1])
        delete_todo(todo_id)
        bot.reply_to(message, f"Todo {todo_id} deleted!")
    if (message.text.split(' ', 1)[0] == '/delete' and llen == 1):
        bot.reply_to(
            message, "Please provide a task description. Use: /delete <task_id>")


setup_db()

bot.polling(none_stop=True)
