
# TravelEase Travel Assistant

TravelEase is a virtual travel assistant built using Streamlit. It helps users with travel-related queries and tasks, providing concise and helpful responses while maintaining a friendly and professional tone. The assistant uses user profile information, including past and upcoming trips, credit card offers, and user preferences, to provide personalized recommendations and references.

## Table of Contents

1. [Getting Started](#getting-started)
2. [App Structure](#app-structure)
3. [Modules](#modules)
    - [app.py](#app-py)
    - [auth.py](#auth-py)
    - [chat.py](#chat-py)
    - [config.py](#config-py)
    - [map_utils.py](#map-utils-py)
    - [google_reviews.py](#google-reviews-py)
    - [ui_components.py](#ui-components-py)
    - [api_client.py](#api-client-py)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [Contributing](#contributing)
7. [License](#license)

## Getting Started

To get started with the TravelEase Travel Assistant, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo/TravelEase.git
    cd TravelEase
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the root directory and add your environment variables:
    ```env
    API_MODE=huggingface
    AWS_REGION=your_aws_region
    AWS_ACCESS_KEY_ID=your_aws_access_key_id
    AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
    HF_EMAIL=your_huggingface_email
    HF_PASS=your_huggingface_password
    ANTHROPIC_API_KEY=your_anthropic_api_key
    GOOGLE_MAPS_API_KEY=your_google_maps_api_key
    ```

4. Run the application:
    ```bash
    streamlit run app.py
    ```

## App Structure

The TravelEase Travel Assistant is structured into several modules, each responsible for specific functionalities. Here's an overview of the key modules:

## Modules

### app.py

The main entry point of the application. It initializes the Streamlit app, sets up the session state, and handles the main flow of the application.

#### Functions

- `main()`: The main function that initializes the Streamlit app, sets up the session state, and handles the main flow of the application.

### auth.py

Handles user authentication and session management.

#### Functions

- `init_session_state()`: Initializes the session state with default values.
- `authenticate(username, password)`: Authenticates the user by checking the username and password against the stored user data.
- `login()`: Displays the login form and handles the login process.
- `logout()`: Logs out the user by clearing the session state.
- `require_login(func)`: A decorator that requires the user to be logged in to access a function.

### chat.py

Handles the chat functionality, including displaying messages, invoking the chat model, and displaying location information and maps.

#### Functions

- `show_map_callback()`: Sets the session state to show the map.
- `hide_map_callback()`: Sets the session state to hide the map.
- `select_location(index)`: Sets the selected location index in the session state.
- `image_to_base64(img)`: Converts an image to a base64 string.
- `initialize_session_state()`: Initializes the session state for the chat.
- `display_welcome_message()`: Displays the welcome message for the user.
- `display_messages()`: Displays the chat messages.
- `start_chat()`: Starts the chat session and handles the chat flow.

### config.py

Contains configuration constants and loads environment variables.

#### Constants

- `USERS_FILE`: Path to the users file.
- `USER_PROFILES_FILE`: Path to the user profiles file.
- `LOGO_PATH`: Path to the logo image.
- `ICON_PATH`: Path to the icon image.
- `CLAUDE_MODEL_ID`: ID of the Claude model.
- `API_MODE`: The API mode to use (huggingface, bedrock, or native_claude).
- `USE_GOOGLE_MAPS`: Flag to use Google Maps for geocoding.
- `GOOGLE_MAPS_API_KEY`: API key for Google Maps.
- `TravelEase_PROMPT`: The prompt used for the TravelEase travel assistant.
- `MAP_CATEGORIES`: Categories of locations to display on the map.

### map_utils.py

Handles map-related functionalities, including extracting locations from text, geocoding locations, and creating maps.

#### Functions

- `extract_locations_llm(text, api_client)`: Extracts locations from text using a language model.
- `get_coordinates_google(location)`: Gets the coordinates of a location using Google Maps.
- `get_coordinates_nominatim(location)`: Gets the coordinates of a location using Nominatim.
- `get_coordinates(location)`: Gets the coordinates of a location using the configured geocoding service.
- `create_map(locations)`: Creates a map with the specified locations.

### google_reviews.py

Handles fetching and summarizing Google reviews for hotels.

#### Classes

- `GoogleReviews`: A class for fetching and summarizing Google reviews.

#### Functions

- `get_place_id(place_name, location=None)`: Gets the place ID for a given place name and location.
- `get_reviews(place_name, location=None, max_reviews=5)`: Gets the reviews for a given place name and location.
- `summarize_reviews(reviews, api_client)`: Summarizes the reviews using a language model.
- `get_hotel_reviews(hotel_name, location=None, max_reviews=5)`: Gets the reviews for a given hotel name and location.
- `get_hotel_reviews_summary(hotel_name, api_client, location=None, max_reviews=5)`: Gets the summary of reviews for a given hotel name and location.

### ui_components.py

Handles UI components and styling.

#### Functions

- `set_custom_css()`: Sets custom CSS for the application.
- `render_sidebar()`: Renders the sidebar with quick links and user information.
- `add_trip_ui(trip_type)`: Displays the UI for adding a new trip.

### api_client.py

Handles API client initialization and model invocation.

#### Functions

- `initialize_api_client()`: Initializes the API client based on the configured API mode.
- `invoke_model(prompt, api_client, user_profile)`: Invokes the language model with the given prompt and user profile.
- `classify_topic(prompt, api_client)`: Classifies the topic of the given prompt using the language model.
- `format_trip_details(trip)`: Formats the details of a trip for display.
- `format_credit_card_info(card)`: Formats the information of a credit card for display.
- `format_preferences(preferences)`: Formats the user preferences for display.

## Usage

To use the TravelEase Travel Assistant, follow these steps:

1. Start the application by running `streamlit run app.py`.
2. Log in using the provided login form.
3. Use the chat interface to ask travel-related questions.
4. View location information and maps for the extracted locations.
5. View hotel reviews and insights for the selected hotels.

## Configuration

The TravelEase Travel Assistant can be configured using environment variables. Create a `.env` file in the root directory and add the following variables:

- `API_MODE`: The API mode to use (huggingface, bedrock, or native_claude).
- `AWS_REGION`: The AWS region for the Bedrock client.
- `AWS_ACCESS_KEY_ID`: The AWS access key ID for the Bedrock client.
- `AWS_SECRET_ACCESS_KEY`: The AWS secret access key for the Bedrock client.
- `HF_EMAIL`: The Hugging Face email for the Hugging Face client.
- `HF_PASS`: The Hugging Face password for the Hugging Face client.
- `ANTHROPIC_API_KEY`: The Anthropic API key for the native Claude client.
- `GOOGLE_MAPS_API_KEY`: The API key for Google Maps.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any bugs, feature requests, or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
```
In case of any difficuilty in setup, read history.txt file on the commands I ran to setup it in my local

