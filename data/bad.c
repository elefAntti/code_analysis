void f(int);

int global = 42;
static int static_global = 43;

void do_stuff(void)
{
    f(123);
}

void lots_of_params(int i1, int i2, int i3, int i4, int i5, int i6, int i7,int i8)
{
    f(i1);
    f(i2);
    f(i3);
    f(i4);
    f(i5);
    f(i6);
    f(i7);
    f(i8);
}

int sum(int i)
{
    static int accu = 0;
    accu += i;
    return accu;
}