def test():
    funcs = []
    for i in range(3):

        def f():
            return i

        funcs.append(f)
    for f in funcs:
        print(f())


test()
