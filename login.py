import os
import inquirer


def get_users_with_passwords():
    lines = (
        [l.strip() for l in open("./users.txt", "r").readlines()]
        if os.path.exists("./users.txt")
        else []
    )
    return dict([l.split(",") for l in lines if l])


def authenticate_user(username, password):
    users_with_passwords = get_users_with_passwords()
    return users_with_passwords.get(username) == password


def cli_login():
    users_with_passwords = get_users_with_passwords()
    usernames = list(users_with_passwords.keys())
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
    answers = inquirer.prompt(questions)
    if answers is None:
        print("Bye!")
        return exit(0)
    answer = answers["username"]
    if answer == "Create new user":
        questions = [
            inquirer.Text("username", message="Enter your name"),
            inquirer.Password("password", message="Enter a password"),
        ]
        answers = inquirer.prompt(questions)
        uname = answers["username"]
        if uname in usernames:
            print("User already exists")
            return cli_login()
        with open("users.txt", "a") as f:
            pwd = answers["password"]
            f.write(f"\n{uname},{pwd}")
        return uname
    pwd = inquirer.password("Enter your password")
    if authenticate_user(answer, pwd):
        return answer
    print("Incorrect password")
    return cli_login()
