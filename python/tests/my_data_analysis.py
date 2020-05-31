from codex import start_recording

start_recording()

a = 6
b = 2 * a
results = []
for i in range(2):
    c = a + b * i
    results.append(c ** 2)


def f(x):
    d = sum([i for i in range(3)])
    return x - d + a


print(f(sum(results)))
