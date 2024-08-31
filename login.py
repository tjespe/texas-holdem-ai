import os
import inquirer


def login():
    lines = (
        [l.strip() for l in open("./users.txt", "r").readlines()]
        if os.path.exists("./users.txt")
        else []
    )
    users_with_passwords = [l.split(",") for l in lines if l]
    usernames = [username for username, pwd in users_with_passwords]
    options = usernames + ["Create new user"]
    questions = [
        inquirer.List(
            "username",
            message="What is your name?",
            choices=options,
            autocomplete=True,
            carousel=True,
            default=options[0],
        ),
    ]
    answer = inquirer.prompt(questions)["username"]
    if answer == "Create new user":
        questions = [
            inquirer.Text("username", message="Enter your name"),
            inquirer.Password("password", message="Enter a password"),
        ]
        answers = inquirer.prompt(questions)
        with open("users.txt", "a") as f:
            f.write(f"\n{answers['username']},{answers['password']}")
        return answers["username"]
    pwd = input("Enter your password: ")
    pwd_map = dict(users_with_passwords)
    if pwd_map.get(answer) == pwd:
        return answer
    print("Incorrect password")
    return login()
