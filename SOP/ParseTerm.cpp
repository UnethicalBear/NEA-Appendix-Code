#include "ParseTerm.h"
#include <iostream>
/*
###                Getters & Setters: ParseTerm          ###

Use: These functions are public methods to get and set private variables of the ParseTerm class.

*/

ParseTerm::ParseTerm() {
	termContents = {};
}

ParseTerm::ParseTerm(std::vector<ParseTokenVariable> term) {
	this->termContents = term;
}


void ParseTerm::setTermContents(std::vector<ParseTokenVariable> newContents) {
	this->termContents = newContents;
}
std::vector<ParseTokenVariable> ParseTerm::getTermContents() {
	return this->termContents;
}

bool ParseTerm::termContainsVariable(std::string variable) {
	for (ParseTokenVariable tok : termContents) {
		if (tok.getData() == variable) {
			return true;
		}
	}
	return false;
}

bool ParseTerm::termContainsVariable(ParseTokenVariable variable) {
	for (ParseTokenVariable tok : termContents) {
		if (tok.getData() == variable.getData()){
			return true;
		}
	}
	return false;
}

// This function is used to erase a variable from a term
void ParseTerm::eraseVariable(char variable) {
	std::string _var; // create a new empty string
	_var += variable; // adding the char acts as typecasting here
	for (ParseTokenVariable tok : termContents) { // iterate over the internal array of tokens
		if (tok.getData() == _var) { // if this token is the required variable to be erased
			termContents.erase(termContents.begin() + // then get the position of the current token
				std::distance(termContents.begin(),   // and erase it from the list
					std::find(termContents.begin(),   // thus removing the token from the term
						termContents.end(), 
						tok
					)
				)
			);
		}
	}
}


int ParseTerm::termLength() {
	return termContents.size();
}

std::string ParseTerm::getString() {
	std::string output = "";
	for (ParseTokenVariable item : getTermContents()) {
		output += item.getData();
		if (item.isTokenInverted()) {
			output += "#";
		}
	}
	return output;
}