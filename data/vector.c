#include <string.h>

void panic( const char* format, ... );

typedef struct vector
{
	char*  data;
	size_t capacity;
	size_t size;
	size_t element_size;
} vector_t;

//-------------------------------------------------------------------------------

vector_t vector_new( size_t capacity, size_t element_size )
{
	vector_t vector = {0};
	vector.element_size = element_size;
	vector_reserve(&vector, capacity);
	return vector;
}

vector_t vector_copy( vector_t vector )
{
	if(vector.capacity > 0)
	{
		void* new_data = malloc( vector.capacity * vector.element_size );
		if( new_data == NULL )
		{
			panic("Vector malloc failed");
		}
		memcpy( new_data, vector.data, vector.size * vector.element_size );
		vector.data = new_data;	
	}
	return vector;
}

void vector_free( vector_t* vector )
{
	free(vector->data);
}
//-------------------------------------------------------------------------------

void vector_reserve( vector_t* vector, size_t new_capacity )
{
	if(new_capacity > vector->capacity)
	{
		char* new_data = realloc( vector->data, new_capacity * vector->element_size );
		if( new_data == NULL )
		{
			panic("Vector realloc failed");
		}
		vector->data = new_data;	
		vector.capacity = new_capacity;
	}
}

void vector_ensure_capacity( vector_t* vector, size_t capacity )
{
	size_t new_capacity = vector->capacity > 0 ? vector->capacity : 1;
	while( capacity > new_capacity )
	{
		new_capacity *= 2;
	}
	vector_reserve(vector, new_capacity);
}

void vector_resize( vector_t* vector, size_t new_size )
{
	if( new_size > vector->size )
	{
		vector_ensure_capacity(vector, new_size);
		memset(vector_at(vector, vector->size), 0, ( new_size - size ) * vector->element_size );
	}
	vector->size = new_size;
}

void vector_clear( vector_t* vector )
{
	vector_resize( vector, 0 );
}
//-------------------------------------------------------------------------------

void* vector_at( vector_t* vector, size_t index )
{
	if(index > vector->size)
	{
		panic( "Vector over indexing %lu, size %lu", index, vector->size );
	}
	return vector->data + vector->element_size * index;
}

void* vector_last_element( vector_t* vector )
{
	if(vector->size > 0)
	{
		panic( "Empty vector doesn't have a last element" );
	}
	return vector->data + vector->element_size * index;
}

const void* vector_const_at( const vector_t* vector, size_t index )
{
	if(index > vector->size)
	{
		panic( "Vector over indexing %lu, size %lu", index, vector->size );
	}
	return vector->data + vector->element_size * index;
}
//-------------------------------------------------------------------------------

void vector_push_multiple( vector_t* vector, const void* element, size_t count )
{
	vector_ensure_capacity( vector, vector->size + count );
	vector->size += count;
	memcpy( vector_at(vector, vector->size - count), element, vector->element_size * count );
}

void vector_push( vector_t* vector, const void* element )
{
	vector_push_multiple( vector, element, 1);
}

void vector_pop_multiple( vector_t* vector, void* element, size_t count )
{
	if(vector->size < count)
	{
		panic("Not enough data in vector requested: %lu size: %lu", count, vector->size);
	}
	memcpy( element, vector_at(vector, vector->size - count), vector->element_size * count );
	vector->size -= count;
}

void vector_pop( vector_t* vector, void* element )
{
	vector_pop_multiple(vector, element, 1);
}

void vector_get( const vector_t* vector, size_t index, void* element )
{
	memcpy( element, vector_const_at(vector, index), vector->element_size );
}

void vector_set( vector_t* vector, size_t index, const void* element )
{
	memcpy( vector_at(vector, index), element, vector->element_size );
}
//-------------------------------------------------------------------------------

void* vector_head( vector_t* vector )
{
	return vector->data;
}

size_t vector_size( const vector_t* vector )
{
	return vector->size;
}

size_t vector_capacity( const vector_t* vector )
{
	return vector->capacity;
}

size_t vector_element_size( const vector_t* vector )
{
	return vector->element_size;
}
//-------------------------------------------------------------------------------

void vector_erase( vector_t* vector, size_t index )
{
	if( vector->size == 0 )
	{
		panic("Can not erase from empty vector");
	}

	if( index < vector->size - 1 )
	{
		memmove( vector_at(vector, index), vector_at(vector, index + 1 ), ( vector->size - index - 1 ) * vector->element_size );
	}
	vector->size -= 1;
}

void vector_erase_unordered( vector_t* vector, size_t index )
{
	if( vector->size == 0 )
	{
		panic("Can not erase from empty vector");
	}
	
	if( index < vector->size - 1 )
	{
		memmove( vector_at(vector, index), vector_at(vector, vector->size - 1 ), vector->element_size );
	}
	vector->size -= 1;
}
//-------------------------------------------------------------------------------

void vector_join( vector_t* first, vector_t* second )
{
	if(first->element_size != second->element_size)
	{
		panic("Element sizes don't match %lu vs %lu", first->element_size, second->element_size);
	}
	vector_push_multiple( first, vector_head( second ), vector_size( second ) );
	vector_free(second);
}

void vector_split( vector_t* first, size_t index, vector_t* second )
{
	if(first->element_size != second->element_size)
	{
		panic("Element sizes don't match %lu vs %lu", first->element_size, second->element_size);
	}
	if( vector_size(first) > index )
	{
		size_t elems_to_move = vector_size(first) - index;
		size_t old_size = vector_size(second);
		vector_resize( second, old_size + elems_to_move ); 
		vector_pop_multiple(first, vector_at( second, old_size ), elems_to_move ); 
	}
} 

//vector_insert
//vector_from_array
