# texas-holdem-ai

This is a Texas Hold'em AI inspired by DeepStack that uses Monte Carlo Tree Search to play the game down to a certain depth. As a heuristic, it uses neural networks to evaluate the strength of the hand.

Most of the project is written in Python, but some performance critical parts are written in C++.

## Setup

0. _Recommended_: Set up a virtual environment by running `python -m virtualenv env` and activating it by running `source env/bin/activate`.
1. Install the required packages by running `pip install -r requirements.txt`.
2. Compile the C++ part of the project:
    ```bash
    cd cpp_poker
    cmake ..
    make
    ```
3. _Optional_: Set up the desired game structure (i.e. number of players, types of players, configuration for computer players) in `main.py`.
4. Run the game by running `python main.py`.

**NB**: Trained neural networks are not included in this repository, and the ResolverPlayer will not work without them.

## Training the neural networks

To train neural networks, training data must first be generated. This can be done by running `python generate_training_data.py`. This will fills the `nn/dfs` folder with training data. For effective training, bootstrapping is recommended, i.e. first generating training data for the river and training a neural network on that data, then using that neural network to generate training data for the turn, and so on. Which stage to generate training data for can be set in `generate_training_data.py`.

When training data has been generated, the neural networks can be trained through the notebook `nn/train_nn.ipynb`.

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