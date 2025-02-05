//#include "pch.h"
#include <string>

/*
###                Class: ParseToken          ###

Use: This class is the main class that the 2 types of token, operator and variable, derive from.
It contains the left and right pointers for the nodes in the tree as well as information
about the data stored in the token.

Inherits from: N/A
Parent of : ParseTokenVariable, ParseTokenOperator

Visible to source(internal):	Yes
Visible to dll(external):		No
Abstract?						No

###========================###
*/

class ParseToken {
protected:
	std::string data; // Data should really be private but for some reason visual studio keeps throwing tantrums when I make it private
	// However, protected keeps data hidden so really is a private variable - maybe some polymorphism bug that I can't control?

public:
	ParseToken() {} // Empty constructor allows us to write `ParseToken tok;` without issues
	virtual ~ParseToken() {} // This is a virtual destructor for the class. A virtual function  is a base class member function 
	// that can be redefined in a child class for polymorphism purposes.


	// Getters and Setters for the data component of the class
	// This acts as an interface between the dll's codebase and the protected variable, 'data'
	void setData(std::string newData) {
		data = newData;
	}
	std::string getData() {
		return this->data;
	}
};

/*
###                Class: ParseTokenVariable          ###

Use: This class is a kind of ParseToken designed for boolean variables.

						---

Inherits from:					ParseToken
Parent of:						N/A
						---

Visible to source(internal):	Yes
Visible to dll(external):		No
Abstract?						No

###========================###
*/

class ParseTokenVariable : public ParseToken { // This tells ParseTokenVariable to inherit from ParseToken
	bool isInverted = false;					// whether this is A or NOT(A). Private.
public:
	ParseTokenVariable(std::string variable, bool isInverted) { // Contructor for std::string data format
		this->data = variable;				// This is the name of the variable
		this->isInverted = isInverted;
	}
	ParseTokenVariable(char variable, bool isInverted) {		// Constructor for char data format
		this->data = "";					// Create a string for the variable name
		this->data += variable;				// add the character to it (basically typecasting here)
		this->isInverted = isInverted;		
	}
	bool isTokenInverted() const {			// const function since this can't be changed, improves performance
		return isInverted;					// getter for private value
	}

	bool operator == (const ParseTokenVariable &other) const { // overloads the == operator to allow us to compare 2 tokens
		return (data == other.data && isInverted == other.isInverted);	// check if both inversion and data are equal
	}

	ParseTokenVariable operator ! () {		// overloads the boolean not operator to allow us to invert the parsetoken 
		this->isInverted = !isInverted;
		return *this;	// return the pointer to this ParseTokenVariable for situations like x = !y
	}
};

/*
###                Class: ParseTokenOperator          ###

Use: This class is a kind of ParseToken designed for boolean operators.

						---

Inherits from:					ParseToken
Parent of:						N/A
						---

Visible to source(internal):	Yes
Visible to dll(external):		No
Abstract?						No

###========================###
*/

class ParseTokenOperator : public ParseToken { // This tells ParseTokenVariable to inherit from ParseToken
public:
	ParseTokenOperator(std::string _operator){ // Custom constructor for std::string datatype
		this->data = _operator;		// This is the type of the operator
	}
	ParseTokenOperator(char _operator) { // Custom constructor for char datatype
		this->data = "";// Create a string for the operator type
		this->data += _operator;				// add the character to it (basically typecasting here)
	}
};


