# EXPERIMENT 2: Factorial of a Number

n = int(input("Enter the number: "))

if n < 0:
    print("Factorial can't be defined for a negative number")
else:
    factorial = 1
    for i in range(1, n + 1):
        factorial *= i

    print(factorial)
