#pragma once
#include <vector>
#include <set>
#include "ParseToken.cpp"

/*
###                Class: ParseTerm          ###

Use: This class stores several ParseTokenVariables, denoting that they are linked together
as one term in the Sum of Products Expression.

						---

Inherits from:					N/A
Parent of:						N/A
						---

Visible to source(internal):	Yes
Visible to dll(external):		No
Abstract?						No

###========================###
*/
class ParseTerm {
	std::vector<ParseTokenVariable> termContents;

public:
	ParseTerm();
	ParseTerm(std::vector<ParseTokenVariable> term);

	void setTermContents(std::vector<ParseTokenVariable> newContents);
	std::vector<ParseTokenVariable> getTermContents();

	bool termContainsVariable(std::string variable);
	bool termContainsVariable(ParseTokenVariable variable);

	void eraseVariable(char variable);

	int termLength();

	std::string getString();

	bool operator < (const ParseTerm& p) const {
		return this->termContents.size() < p.termContents.size();
	}

	bool operator == (const ParseTerm& other) const {
		return (termContents == other.termContents);
	}

};

