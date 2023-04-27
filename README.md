# Self Reservation (Shahrood university technology)

Self-Reservation Tool for Shahrood University of Technology

## Purpose

This tool allows students of Shahrood University of Technology to make meal reservations at the Self cafeteria automatically.

## Installation

1. Clone the repository:

```
git clone https://github.com/Warm-Hearted-Snowman/Predict_Car_Price_with_MachineLearning
```

2. Install the required dependencies:

```
pip install -r requirements.txt
```

3. Run the program:

```
python main.py
```


## Usage Details

This program uses two modules: 
* `fetch_data` : Fetches data needed for reservations from server.
* `module`: Reads the stored reservation data.

You will need to provide your login credentials to the program when prompted. If you have already logged in before, the program will use your saved cookies to avoid logging in again.

The program will then attempt to make meal reservations for breakfast, lunch, and dinner for the next available days. If a meal is already reserved for a particular day, the program will skip that day.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details. 
