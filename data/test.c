

int sum(int* array, int len)
{
  int accu = 0;
  while(len-- > 0)
  {
    accu += array[len];
  }
  return accu;
}

void bar(int* array, int len)
{
}