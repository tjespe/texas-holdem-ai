# texas-holdem-ai

This is a Texas Hold'em AI inspired by DeepStack that uses Monte Carlo Tree Search to play the game down to a certain depth. As a heuristic, it uses neural networks to evaluate the strength of the hand.

Most of the project is written in Python, but some performance critical parts are written in C++.

## Setup

0. _Recommended_: Set up a virtual environment by running `python -m virtualenv env` and activating it by running `source env/bin/activate`.
1. Install the required packages by running `pip install -r requirements.txt`.
2. Install CMake and ensure that a C++ compiler is available.
3. Compile the C++ part of the project:
   ```bash
   cd cpp_poker
   cmake ..
   make
   ```
4. _Optional_: Set up the desired game structure (i.e. number of players, types of players, configuration for computer players) in `main.py`.
5. Run the game by running `python main.py`.

## Simplifications

The following simplifications have been made to the game:

- When using the resolver (e.g. through the ResolverPlayer), only two players are supported.
- There are no side pots. This has two consequences:
  1. If a player goes all-in, the other players can only call or fold.
  2. It is not possible to raise by more than the player with the smallest stack can call.

## Project structure

The main components of this project are:

- A poker "oracle" written in C++ that can evaluate the strength of hands and compare them. Defined in `Oracle.cpp`, `CheatSheet.cpp`, and `CardCollection.cpp`.
- A Monte Carlo Tree Search implementation in Python that can play Texas Hold'em. Defined in `resolver.py`.
- Neural networks used as heuristics to limit the search space. Defined in the files in the `nn` subdirectory.
- A game manager that can run games between different players. Defined in `GameManager.py`.
- A state manager that implements the rules of Texas Hold'em and how different actions lead to different states. Defined in `state_management.py`.
