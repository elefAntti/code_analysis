int f(void);
void g(void);


void simple_switch_test(void)
{
    switch(f() + f())
    {
        case 1:
        case 2:
        {
            g();
        }
        break;
        case 3:
            g();
        break;
        case 4:
        {
            if(f() == 3)
            {
                if(f() == 4)
                    g();
            }
            else
            {
                f();
            }
        }
        break;
        default:
        f();
        g();
    }
}