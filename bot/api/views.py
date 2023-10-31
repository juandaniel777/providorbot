from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from django.conf import settings
from django.shortcuts import get_object_or_404
from bot.models import Users, Orders, Dishes, OrderDishes, Ratings
import random
import datetime
from bot.utils.twilio import send_whatsapp_message
from bot.utils.gpt4 import intention_classification

class MessageView(APIView):
    """
    View to receive message from Twilio sources, process it
    """
    def gather_order_details(self, order):
        # Get the dishes for this order
        order_dishes = OrderDishes.objects.filter(order=order)
        
        # Extracting dish details for the message
        details = []
        for od in order_dishes:
            dish = od.dish
            dish_details = {
                "name": dish.dish_name,
                "description": dish.dish_description,
                "price": dish.price,
                "course": dish.course,
                "chef": dish.chef_name,
                "dietaries": dish.dietaries
            }
            details.append(dish_details)
        return details

    def get_latest_order(self, user):
        """
        Returns the latest order placed by the user.

        Args:
        - user (Users model instance): The user for whom to fetch the latest order.

        Returns:
        - Orders model instance: The latest order placed by the user or None if no order found.
        """
        
        try:
            # Retrieve the latest order for the user based on the order_time
            latest_order = Orders.objects.filter(user=user).latest('order_time')
            return latest_order
        except Orders.DoesNotExist:
            # If no order is found for the user
            return None

    def add_rating(self, user, order, rating_value, feedback):
        """
        Insert a new rating row into the Ratings table.

        Parameters:
        - user: The user object.
        - order: The order object.
        - rating_value: The numerical rating value (e.g., 1-5).
        - feedback: The text feedback from the user.

        Returns:
        - The created Ratings object.
        """
        rating = Ratings(user=user, order=order, rating=rating_value, original_feedback=feedback)
        rating.save()
        return rating

    def format_ratings_message(self, user):
        """
        Format the rating data for a given user into a readable message.

        Parameters:
        - user: The user object.

        Returns:
        - A string containing the formatted ratings data.
        """
        ratings = Ratings.objects.filter(user=user)
        
        if not ratings.exists():
            return f"No ratings found for user with WhatsApp number {user.whatsapp_number}."
        
        formatted_message = f"Ratings for user with WhatsApp number {user.whatsapp_number}:\n\n"
        
        for rating in ratings:
            order_time = rating.order.order_time
            order_status = rating.order.order_status
            rating_value = rating.rating
            feedback = rating.original_feedback
            
            formatted_message += f"Order Time: {order_time}\n"
            formatted_message += f"Order Status: {order_status}\n"
            formatted_message += f"Rating: {rating_value}\n"
            formatted_message += f"Feedback: {feedback}\n"
            formatted_message += "-"*30 + "\n"  # Separator for readability
        
        return formatted_message



    def create_random_order(self, user):
        # Create an order for the user
        right_now = datetime.datetime.now()
        order = Orders.objects.create(user=user, order_time=right_now, order_status="delivered")

        # Pick two random dishes for mocking and create order_dishes records
        dishes = list(Dishes.objects.all())
        selected_dishes = random.sample(dishes, 2)
        for dish in selected_dishes:
            OrderDishes.objects.create(order=order, dish=dish) 
        return order
    
    def format_order_message(self, order_details):
        # Format the order details for the message
        message = "Your order includes:\n"
        for detail in order_details:
            message += "\n===\n"
            message += (
                f"Dish: {detail['name']}\n"
                f"Price: {detail['price']}\n"
                f"Course: {detail['course']}\n"
            )
            
        return message
    
    def post(self, request):
        # Ensure request is from Twilio
        # ... your Twilio validation code here ...

        # Extract incoming WhatsApp number
        whatsapp_number = request.data.get('From')  # assuming 'From' contains the number
        user_message = request.data.get('Body')
        sender_number = settings.TWILIO_NUMBER # Reply using this Twilio WhatsApp number

        if not whatsapp_number:
            return Response({"message": "No sender information found."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user exists or create a new one
        user, created = Users.objects.get_or_create(whatsapp_number=whatsapp_number)

        # If it's a new user, create a random order and send a welcome message
        if created:
            # Create an order for the user
            order = self.create_random_order(user)
            # Gather order details (assuming this is some function or method you'll create)
            order_details = self.gather_order_details(order)  

            # Send welcome message with order details
            
            send_whatsapp_message(
                sender_number,
                whatsapp_number, 
                f"""Hello from Providoor Bot! Your order {order_details} has been delivered.\n 
                We would love to hear your feedback!\n
                Describe your experience or simply give a rating from 1 to 10.\n\n
                (Mockup Commands): \n\nREPLY "/new" to place a new order.\n
                REPLY "/latest" to check the latest order status.\n
                REPLY "/recommend" to get recommendations.\n
                REPLY "/ratings" to get all my ratings.\n
                REPLY "/help" to check this message again.\n
                """
            )
        else:
            if user_message=="/new":
                # Create an order for the user
                random_order = self.create_random_order(user)
                # Gather order details (assuming this is some function or method you'll create)
                order_details = self.gather_order_details(random_order)  
                formatted_order_message = self.format_order_message(order_details)
                send_whatsapp_message(
                    sender_number,
                    whatsapp_number,  #whatsapp_number
                    f"Order creation:\n {formatted_order_message}"
                )
                return Response({"message": "Providoor bot: Create a random order", "data": formatted_order_message}, status=status.HTTP_200_OK)
            elif user_message=="/latest":
                # Get the latest order for the user
                latest_order = self.get_latest_order(user)
                
                if latest_order is None:
                    send_whatsapp_message(
                        sender_number,
                        whatsapp_number,  #whatsapp_number
                        "No pending orders found."
                    )
                else:
                    # Gather order details (assuming this is some function or method you'll create)
                    order_details = self.gather_order_details(latest_order)  
                    formatted_order_message = self.format_order_message(order_details)
                    send_whatsapp_message(
                        sender_number,
                        whatsapp_number,  #whatsapp_number
                        f"Latest order: \n{formatted_order_message}"
                    )
                return Response({"message": "Providoor bot: Returned the latest order"}, status=status.HTTP_200_OK)
            elif user_message=="/recommend":
                send_whatsapp_message(
                    sender_number,
                    whatsapp_number, 
                    "Recommendations coming soon!"
                )
                return Response({"message": "Providoor bot: Provide recommendations"}, status=status.HTTP_200_OK)
            elif user_message=="/ratings":
                all_user_ratings_message = self.format_ratings_message(user)
                if all_user_ratings_message is None:
                    send_whatsapp_message(
                        sender_number,
                        whatsapp_number, 
                        "No ratings found."
                    )
                else:
                    send_whatsapp_message(
                        sender_number,
                        whatsapp_number, 
                        f"All Ratings \n{all_user_ratings_message}"
                    )
                return Response({"message": "Providoor bot: All user ratings", "data": all_user_ratings_message}, status=status.HTTP_200_OK)
            elif user_message=="/help":
                send_whatsapp_message(
                    sender_number,
                    whatsapp_number, 
                    """
                    (Mockup Commands): \n\nREPLY "/new" to place a new order.\n
                    REPLY "/latest" to check the latest order status.\n
                    REPLY "/recommend" to get recommendations.\n
                    REPLY "/ratings" to get all my ratings.\n
                    REPLY "/help" to check this message again.\n
                    """
                )
                return Response({"message": "Providoor bot: Help message"}, status=status.HTTP_200_OK)
            # If it's an existing user, check if they have any pending orders
            latest_order = self.get_latest_order(user)
            if latest_order is None:
                # TODO: No pending orders found, giving some recommendations
                pass
            else:
                response = intention_classification(user_message)
                if(response['function_name'] == "get_user_rating"):
                    #Insert rating into database
                    rating = self.add_rating(user, latest_order, response['response']['rating'], user_message)
                    print(rating)
                    send_whatsapp_message(
                        sender_number,
                        whatsapp_number,
                        "Thanks for your feedback! We will use it for future recommendations."
                    )
                    
        return Response({"message": "Providoor bot: WhatsAPP message Replied"}, status=status.HTTP_200_OK)

class WhatsAppMessageView(APIView):
    # This is a test method to send WhatsApp message
    def post(self, request):
        # Extract incoming WhatsApp number
        whatsapp_number = request.data.get('From')  # assuming 'From' contains the number
        user_message = request.data.get('Body')
        sender_number = settings.TWILIO_NUMBER # Reply using this Twilio WhatsApp number
        send_whatsapp_message(
            sender_number,
            whatsapp_number,
            "Hello from Providoor Bot!"
        )
        return Response({"message": "WhatsAPP Test Message Sent"}, status=status.HTTP_200_OK)

class PingView(APIView):
    def get(self, request):
        return Response({"message": "pong"}, status=status.HTTP_200_OK)
    
