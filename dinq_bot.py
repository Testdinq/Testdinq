import telebot
from telebot import types

# Your bot token
bot_token = '6628858874:AAHghVqbWxbRVIbxuHGwAce2cveZKo5ueCQ'

# Admin's Telegram user ID
admin_id = '1968866234'

# Initialize the bot
bot = telebot.TeleBot(bot_token)

# Dictionary to store uploaded books as File objects
uploaded_books = {}

# Dictionary to store book file IDs associated with their names
book_file_ids = {}

# Dictionary to store book prices
book_prices = {}

# Dictionary to store user book selections
user_selections = {}

# Flag to track if admin has uploaded books
admin_has_uploaded_books = False

# Function to handle /start command for admins
@bot.message_handler(commands=['start'])
def start_admin(message):
    if str(message.chat.id) == admin_id:
        global admin_has_uploaded_books
        admin_has_uploaded_books = False
        markup = types.ReplyKeyboardRemove()
        msg = bot.send_message(message.chat.id, "Welcome, Admin! Please upload a book now.", reply_markup=markup)
        bot.register_next_step_handler(msg, upload_book)
    else:
        bot.send_message(message.chat.id, "Welcome! Please use the /buy command to buy books.")

# Function to handle book uploads by admin
@bot.message_handler(content_types=['document'])
def upload_book(message):
    if str(message.chat.id) == admin_id:
        book_name = message.document.file_name

        # Save the book as a File object
        book_file = bot.get_file(message.document.file_id)
        uploaded_books[book_name] = book_file

        # Store the file ID associated with the book name
        book_file_ids[book_name] = message.document.file_id

        # Ask for the book price
        bot.send_message(admin_id, f"Book '{book_name}' uploaded successfully! Please specify the price of the book:")
        bot.register_next_step_handler(message, set_book_price, book_name)

# Function to set the price for a book
def set_book_price(message, book_name):
    if str(message.chat.id) == admin_id:
        price = message.text

        if price.isdigit():
            book_prices[book_name] = int(price)
            bot.send_message(admin_id, f"Price for '{book_name}' set to {price} USD.")
        else:
            bot.send_message(admin_id, "Please enter a valid numeric price for the book.")

# Function to handle /buy command for users
@bot.message_handler(commands=['buy'])
def start_user(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Welcome! Please choose a book to buy.")

    if bool(book_prices):  # Check if there are book prices
        # Display list of available book names and prices
        book_names = list(uploaded_books.keys())
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=1)
        
        for book_name in book_names:
            book_price = book_prices.get(book_name, "Price not set")
            markup.add(f"{book_name} - {book_price} USD")
        
        msg = bot.send_message(user_id, "Available Books:", reply_markup=markup)
        bot.register_next_step_handler(msg, select_book)
    else:
        bot.send_message(user_id, "No books are available for purchase at the moment.")

# Function to handle book selection by users
def select_book(message):
    user_id = message.chat.id
    book_name = message.text.split(' - ')[0]  # Extract the book name from the user's message

    if book_name in uploaded_books:
        # Ask the user to make a payment
        bot.send_message(user_id, f"Please deposit the money to this bank account:\nBank Name: XYZ Bank\nAccount Number: 123456789")

        # Ask the user to attach a screenshot photo of their payment
        bot.send_message(user_id, "Once you've made the payment, please attach a screenshot photo of your payment.")
        
        # Store the selected book name in user's data
        user_selections[user_id] = book_name
    else:
        bot.send_message(user_id, "Book not found. Please choose a book from the list.")

# Function to handle payment screenshot forwarding to admin
@bot.message_handler(content_types=['photo'], func=lambda message: message.chat.id != admin_id)
def forward_payment_screenshot(message):
    user_id = message.chat.id

    if user_id == admin_id:
        bot.send_message(admin_id, "Admin, please use the /start command to upload a book.")
    elif user_id in user_selections:
        # Forward the payment screenshot to the admin
        payment_screenshot = message.photo[-1].file_id
        bot.forward_message(admin_id, user_id, message.message_id)

        # Notify the user that payment is being verified
        bot.send_message(user_id, "Payment is being verified. Please wait for confirmation from the admin.")
    else:
        bot.send_message(user_id, "Please select a book from the list before sending a payment screenshot.")

# Function to send the book file to the user
def send_book_to_user(user_id, book_name):
    if user_id in user_selections:
        try:
            file_id = book_file_ids.get(book_name)
            bot.send_document(user_id, file_id)
            bot.send_message(user_id, "Here is your book. Enjoy your reading!")
        except Exception as e:
            bot.send_message(user_id, "Sorry, there was an error sending the book. Please contact customer service.")
    else:
        bot.send_message(user_id, "No book selection found for this user.")

# Function to handle admin confirmation
@bot.message_handler(func=lambda message: message.text == '1' and str(message.chat.id) == admin_id)
def confirm_payment(message):
    user_id = None

    for user, book_name in user_selections.items():
        if user_selections[user] == book_name:
            user_id = user
            break

    if user_id is not None:
        # Notify the user that payment has been confirmed
        bot.send_message(user_id, "Payment has been confirmed. You can now access and download the book.")
        
        # Send the book to the user
        send_book_to_user(user_id, book_name)
        
        # Clear user's selection
        del user_selections[user_id]
    else:
        bot.send_message(admin_id, "No book selection found for this user.")

# Function to handle admin confirmation failure
@bot.message_handler(func=lambda message: message.text == '2' and str(message.chat.id) == admin_id)
def confirm_payment_failure(message):
    user_id = None

    for user, book_name in user_selections.items():
        if user_selections[user] == book_name:
            user_id = user
            break

    if user_id is not None:
        # Notify the user that payment verification failed
        bot.send_message(user_id, "Payment verification failed. Please contact customer service at 0965227209")
        
        # Clear user's selection
        del user_selections[user_id]
    else:
        bot.send_message(admin_id, "No book selection found for this user.")

# Start the bot
bot.polling()

