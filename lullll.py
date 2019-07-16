from timeit import default_timer as timer


S_PER_UPDATE = 0.033


def main_loop():
    previous = timer()
    lag = 0.0

    while 1:
        current = timer()
        elapsed = current - previous
        previous = current

        lag += elapsed

        while lag >= S_PER_UPDATE:
            update()
            lag -= S_PER_UPDATE

        render()


def process_input():
    print('input')


def update():
    process_input()
    print('update')

# non-blocking!
def render(progress):
    print('render', progress)


def main():
    main_loop()


if __name__ == '__main__':
    main()