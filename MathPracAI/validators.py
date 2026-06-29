def normalize(value):
    return "".join(str(value).lower().split())


def answers_match(user_answer, correct_answer):
    user = normalize(user_answer)
    correct = normalize(correct_answer)

    if user == correct:
        return True

    try:
        return abs(float(user) - float(correct)) < 0.001
    except ValueError:
        pass

    if "," in correct:
        return sorted(user.split(",")) == sorted(correct.split(","))

    return False


def answers_match_problem(user_answer, problem):
    return any(answers_match(user_answer, answer) for answer in problem.acceptable_answers)
