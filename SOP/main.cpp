//main.cpp : Defines the entry point for the DLL application.

// libraries to be included:
#include "pch.h"		// needed for dll
#include <iostream>		// allows output to the console
#include <string>		// allows string datatype
#include <vector>		// allows dynamic list operations
#include <stack>		// allows stack datatype
#include <queue>		// allows the queue and priority_queue datatype
#include <set>			// allows the set datatype
#include <any>			// allows dynamic data types because typeid won't work
#include <exception>	// error handling, input validation etc.
#include <regex>		// regex library for input validation

#include "main.h"		// introduces function definitions to compiler
#include "ParseTerm.h"	// ParseTerm class for boolean simplifacation

const std::string ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"; // Upper case alphabet saved as a constant variable for ease of use.

/* 
The APIENTRY function is standard code to let the application using the library register why it is using it.
The process returns true if the library is being used by another program. Internal OS features, or trying
to link to the library but not, it returns NULL
*/
BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved){
    switch (ul_reason_for_call){
		case DLL_PROCESS_ATTACH:
		case DLL_THREAD_ATTACH:
		case DLL_THREAD_DETACH:
		case DLL_PROCESS_DETACH:
			break;
    }
    return TRUE;
}

/*
###                Function: countOccurences          ###
Use: this function counts the number of times a character appears in a string. 
---
Parameters: in (string): the string to search, search (char): the character to look for
Returns: ctr (int): the number of times the character was found.
---
Visible to dll (external): No
*/
int countOccurrences(std::string in, char search) {
	int ctr = 0;
	for (char c : in)
		if (c == search)
			ctr++;
	return ctr;
}

/*
###                Function: areVectorContentsEqual          ###
Use: This function checks if two lists contain the same information, even if they aren't in the same order.
---
Parameters: vec1, vec2: the 2 lists to check
Returns: true/false (bool)
---
Visible to dll (external): No
*/
template <typename T>		// This means that the lists can contain any data type provided they are the same and can use the == operator
bool areVectorContentsEqual(std::vector<T> vec1, std::vector<T> _vec2) {
	auto vec2 = _vec2;		// create a copy of the second vector so we can manipulate it without worrying about changing the original.
	for (auto& element : vec1) { // iterate over each item in the vector
		if (std::find(vec2.begin(), vec2.end(), element) != vec2.end()) { // if the current item is in the copy of the second
			vec2.erase(vec2.begin() +									  // keeping going, but remove the item from the copy of the 2nd to...
				std::distance(vec2.begin(), find(vec2.begin(), vec2.end(), element)));  // ...prevent duplicates from occuring
		}
		else {
			return false; // this item isnt in both, so the contents are equal
		}
	}
	return (vec2.size() == 0); // if we got here, and the lists are the same, the length of the copy will be 0
}

/*
###                Function: countInvertedPairs          ###
Use: This function checks if how many inverted pairs there are in 2 terms. An inverted pair means that one term contains A and the other A#. 
	 it also returns the variable of the last inverted pair found, e.g. in the above example A would be returned.
---
Parameters: term1, term2 (ParseTerm): the 2 terms to compare.
Returns: the number of inverted terms (int) and the variable of the last inverted term (char)
---
Visible to dll (external): No
*/
std::pair<int, char> countInvertedPairs(ParseTerm term1, ParseTerm term2) {
	int ctr = 0; // number of inverted pairs found
	char lastInvertedPair; // variable of the last inverted pair in the two terms 
	std::vector<ParseTokenVariable> t1 = term1.getTermContents(); 	// first term's contents
	std::vector<ParseTokenVariable> t2 = term2.getTermContents(); 	// second term's contents
	for (int i = 0; i < t1.size(); i++) {							// iterate over the pairs
		auto item = !t1[i];										  	// invert the current item (make A into A#)
		if (std::find(t2.begin(), t2.end(), item) != t2.end()) { 	// if this inverted token is in the second term
			ctr++;													// then we have an inverted pair
			lastInvertedPair = t1[i].getData().c_str()[0];			// and we set the current inverted pair variable to the current char
		}
	}
	return { ctr, lastInvertedPair };								// return the counter and the most recent inverted pair found
}

/*
###                Function: termLengthDifference          ###
Use: 
---
Parameters: the 2 ParseTerms to calculate the length difference of
Returns: a positve integer (or 0) 
---
Visible to dll (external): No
*/
int termLengthDifference(ParseTerm term1, ParseTerm term2) {
	int diff = term1.getTermContents().size() - term2.getTermContents().size(); // get the difference in length
	if (diff < 0)						
		diff *= -1;						// ensure the difference is positive as we only consider the magnitude.
	return diff;
}

int countVariableDifferences(ParseTerm term1, ParseTerm term2) {
	// A variable difference is where 1 term contains a variable that the other does not.
	// E.g. AB + B has a variable difference of 1 since the 1st term contains A but the 2nd doesn't.
	// note that A# + A has a variable difference of 0 since we ignore any inversions
	int ctr = 0; // how many variable differences we have
	std::vector<ParseTokenVariable> t1; // the first term's contents
	std::vector<ParseTokenVariable> t2; // the second term's contents
	if (term1.termLength() > term2.termLength()) { // find the longer term
		t1 = term1.getTermContents(); // the longer term will be first as this is both more efficient
		// and also ensures that all variables are definitely counted
		t2 = term2.getTermContents();
	}
	else {
		t1 = term2.getTermContents();
		t2 = term1.getTermContents();
	}
	for (int i = 0; i < t1.size(); i++) {
		if (std::find(t2.begin(), t2.end(), t1[i]) == t2.end() &&  	// if A is not in term 2 
			std::find(t2.begin(), t2.end(), !t1[i]) == t2.end()) {  // and A# is not in term 2
			ctr++;													// then A is an occurance of a variable difference
		}
	}
	return ctr;
}

std::vector<std::pair<int, int>> findCombinations(int n) {
	std::vector<std::set<int>> checkSet;			// set of values we have already got
	std::vector<std::pair<int, int>> pairsOut;		// pairs of values to return

	for (int i = 0; i < n; i++) {					// iterate up to the max number
		for (int j = 0; j < n; j++) {				// again, iterate up to the max number

			if (i == j) {							// if the indecies are the same, the values will always be the same
				continue;							// so they will never be a valid pair.
			}

			std::set<int> nextSet = { i,j };		// create a set of i and j
			
			// if this set hasn't been generated before (in any order - {2,3} == {3,2} for this purpose),
			if (std::find(checkSet.begin(), checkSet.end(), nextSet) == checkSet.end()) {
				// then we add it to the list of found combinations and create a pair of values to return
				pairsOut.push_back({ i,j }); // this is a valid combination
				checkSet.push_back(nextSet); // but it isn't if we find it again
			}
		}
	}
	return pairsOut;								// return the pairs found
}

// This function finds every unique conbination between a list of ParseTerms so we ensure we compare every possible option
// Inputs are the number of terms (the length of the expression), and the expression itself
std::vector<std::pair<ParseTerm, ParseTerm>> findParseTermCombinations(int n, std::vector<ParseTerm> expr) {
	std::vector<std::pair<int, int>> combinations = findCombinations(n); // find the integer combinations possible
	std::vector<std::pair<ParseTerm, ParseTerm>> output = {};
	for (auto &combination : combinations) {							// we use the possible integer combinations as indecies
		output.push_back({ expr[combination.first], expr[combination.second] }); // to slice the array and create the ParseTerm combinations.
	}
	return output;
}

std::vector<ParseTerm> applyBooleanIdentities(std::vector<ParseTerm> exprIn, std::string &debugStrIn, int &passes) {
	passes++;	// debug: the number of tries needed to get to the simplest form increases for every time this is called
	// note that passes and debugStrIn are pass by reference to avoid complications when recursing.

	// A copy of the input expression to return as output
	std::vector<ParseTerm> exprOut = exprIn;

	// get the simplest possible combinations of parseterms 
	std::vector<std::pair<int, int>> combinationIndicies = findCombinations(exprIn.size());
	std::vector<std::pair<ParseTerm, ParseTerm>> combinations = findParseTermCombinations(exprIn.size(), exprIn);
	
	// iterate over the combinations
	for (int i = 0; i < combinations.size(); i ++) {
		// this is the current pair
		auto &option = combinations[i];

		// get the number of inverted pairs
		std::pair<int, char> invertedPairData = countInvertedPairs(option.first, option.second);
		char invertedPairVar = invertedPairData.second;

		// have we removed a term from the term
		bool removedTerm = false;

		// If the first term contains A AND A#, it will never be true, so remove the term
		if (countInvertedPairs(option.first, option.first).first >= 1) {
			// erase the term
			exprOut.erase(exprOut.begin() + combinationIndicies[i].first);
			// can't do any more simplifying this time around => set removedTerm flag
			removedTerm = true;
		}
		// If the second term contains A AND A#, it will never be true, so remove the term
		if (countInvertedPairs(option.second, option.second).first >= 1) {
			// erase the term
			exprOut.erase(exprOut.begin() + combinationIndicies[i].second);
			// can't do any more simplifying this time around => set removedTerm flag
			removedTerm = true;
		}
		// If we removed a term we can't do anything else this time so go around
		if (removedTerm)
			continue;

		// retrive/calculate the IP (inverted pair count), LD (length difference) & VD (variable difference)
		int IP		= invertedPairData.first;
		int LD		= termLengthDifference(option.first, option.second);
		int VD		= countVariableDifferences(option.first, option.second);

		//std::cout << "IP: " << IP << " LD: " << LD << " VD: " << VD << std::endl;

		// If there is no difference between the terms we can use the identity:
		// 					A + A = A
		// So we need to remove one of the terms
		if (IP + LD + VD == 0) {
			// remove the second term (arbitrary choice, it doesn't matter since they're the same)
			exprOut.erase(exprOut.begin() + combinationIndicies[i].second);
			// record the operation we just did in the debug string
			debugStrIn += ("I0{" + std::to_string(combinationIndicies[i].first) + "-" + std::to_string(combinationIndicies[i].second) + "}");
			// stop simplifying here for this combination
			break;
		}
		// if the terms are the same except they contain just one inverted pair, then:
		// 					A#B + AB = B
		// So we remove the inverted pair and one of the terms
		else if (LD + VD == 0 && IP == 1) {
			// Remove the inverted pair from the first term
			exprOut[combinationIndicies[i].first].eraseVariable(invertedPairVar);
			// Erase the second term
			exprOut.erase(exprOut.begin() + combinationIndicies[i].second);
			// record the operation we just did in the debug string
			debugStrIn += ("I1{" + std::to_string(combinationIndicies[i].first) + "-" + std::to_string(combinationIndicies[i].second) + "}");
			// stop simplifying here for this combination
			break;
		}
		// if one of the terms contains 1 variable the other doesn't and otherwise they are the same
		// then we can use the identity:
		//					A + AB = A
		// So we remove the longer of the two terms
		else if (LD == 1&& VD == 1 && IP == 0) {
			// If the first term is longer
			if (option.first.termLength()> option.second.termLength()) {
				// erase the first term
				exprOut.erase(exprOut.begin() + combinationIndicies[i].first);
			} // otherwise 
			else {
				// erase the second term
				exprOut.erase(exprOut.begin() + combinationIndicies[i].second);
			}
			// record the operation we just did in the debug string
			debugStrIn += ("I2{" + std::to_string(combinationIndicies[i].first) + "-" + std::to_string(combinationIndicies[i].second) + "}");
			// stop simplifying here for this combination
			break;
		}
		// if one of the terms is one longer than the other with a variable difference of 1 but the terms#
		// also contain a single inverted pair then we can use the identity:
		// 					A + A#B = A + B
		// Therefore we remove the inverted pair in the larger of the two terms.
		else if (LD == 1 && VD == 1 && IP == 1) {
			// if the first term is longer than the second
			if (option.first.termLength() > option.second.termLength()) {
				// remove the inverted pair in the first
				exprOut[combinationIndicies[i].first].eraseVariable(invertedPairVar);
			}
			else {
				// otherwise remove the inverted pair in the second
				exprOut[combinationIndicies[i].second].eraseVariable(invertedPairVar);
			}
			// record the operation we just did in the debug string
			debugStrIn += ("I3{" + std::to_string(combinationIndicies[i].first) + "-" + std::to_string(combinationIndicies[i].second) + "}");
			// stop simplifying here for this combination
			break;
		}
	}

	// If the contents before and after identities were applied are the same, no more indenties can be applied,
	// so the algorithm is complete. Otherwise, recursion takes place and keeps simplifying and repeats the process
	// again. This is important because as the simplifacation process happens, new identities can be applied. If we
	// only interate once, terms will be missed, or "ghost terms" created.
	if (!areVectorContentsEqual(exprIn, exprOut)) { // this checks the contents, not the order
		return applyBooleanIdentities(exprOut, debugStrIn, passes); // recurse again
	}
	return exprOut; // else we cannot simplify further, return what we've got
}

const char* sumOfProducts(const char* truthTable, const int rowWidth) {
	/*
	FUNCTION:		sumOfProducts
	INPUTS:			truth table (string), rowWidth (integer)
	OUTPUTS:		boolean expression (string)
	CALLS:			N/A
	VISIBLE TO DLL: yes

	EXPLANATION:

	Python cannot pass the complex data type to the function directly, we must pre - process it to ensure
	that the sum of products calculator gets the data it needs. The truth table is compressed to a string and
	then decompressed back into an array ready for the calculator to implement.

	*/

	if (strlen(truthTable) % rowWidth) {
		// check if the truth table is complete. This will be called if there is extra data supplied.
		return " @@0@@ERROR: TRUTH TABLE IS NOT CONSISTENT";
	}
	int rows = strlen(truthTable) / rowWidth;

	// calculate how many rows will be in the truth table. e.g. if 30 booleans were recieved and each row is 3
	// wide then there will be 10 rows in the truth table.

	std::vector<std::vector<bool>> _truthTable;				// truth table 2D array
	static std::string output = "";							// the SOP output
	output.erase(output.begin(), output.end());				// we need to return a static string, but if this has been called before output will already have a value. 
	// therefore, the contents of output is completely erased.
	std::string termOutput = "";							// each term in the output
	bool nextValue;											// next term to evaluate 

	for (int i = 0; i < rows; i++) {						// for each row in the truth table
		std::vector<bool> currentRow = {};					// create a new list for this row's data
		for (int j = 0; j < rowWidth; j++) {				// iterate over the columns in the row
			nextValue = (truthTable[(i * rowWidth) + j]) == '1' ? 1 : 0;	// i * rowWidth + j gives the next index of the row/column coordinate, and coverts it to a numeric value
			currentRow.push_back(nextValue);				// add this numeric value to the current list
		}
		_truthTable.push_back(currentRow);					// add the current row to the 2D array and repeat
	}
	
	for (auto &row : _truthTable) {		// iterate through all rows of the truth table

		if (row.size() == 0) {
			continue;					// ignore empty rows to stop index errors
		}

		if (row.back()) {				// if the output of the truth table is 1...
			row.pop_back();				
			/*
			this row gives an output of 1, so we need to add it to our expression. we also remove the output 
			as it's no longer needed and will confuse the alogrithm into thinking an output is an input. Then
			we work out why the row resulted in 1, as this is a term in the SOP expression.
			*/

			termOutput = "";
			for (int col = 0; col < row.size(); col++){	
				// iterate through all columns in row to add the terms to the SOP expression
				termOutput += ALPHABET[col];
				if (!row[col]) {				// this term needs to be 0 for the output to be 1, so add a # to the end
					termOutput += "#";			// the # indicates the NOT operator
				}
			}
			output += (termOutput + "+");		// add this term to the expression
		}
	}
	if (output.size() > 0) { // if we actually got an output string
		output.pop_back();	// this algorithm always generates an extra + character at the end so we remove it.

		if (countOccurrences(output, '+') == rows-1) {
			output = "1";	// in this case, every term gives an output of 1 so Q=1 as a constant value
		}
	}
	else {					// if the string was empty, there is no term that causes Q=1
		output = "0";		// so therefore Q=0 (a constant value).
	}
	
	// Now we have sucesfully generated the SOP, we need to package the SOP back into the string to tell Python that 
	// generation was successfull and that no errors occurred. 
	
	output += "@@1@@Sucessfully Generated SOP";
	// Format of output is SOP_STRING@@SUCCESS@@OTHER_MESSAGES where @@ is used to seperate.
	return output.c_str(); // return the final SOP string back to the Python program.
}

std::string reverseString(std::string strToReverse) {
	std::stack<char> _stack = {};		// create the character stack that will be used to reverse a string
	std::string reversed = "";			// create the reference to the reversed string

	for (char c : strToReverse) {		// iterate over the input string
		_stack.push(c);					// for each character, push to the stack
	}
	for (char c : strToReverse) {		// with the completed stack, iterate over the stack 
		reversed += _stack.top();		// get the top element of the stack and add it to the reversed string
		_stack.pop();					/* C++'s pop() method doesn't return the object popped, so having used
		// 								   the top method to get the item we now can pop it to clear it from
		//								   the stack */
	}
	return reversed;
}

std::vector<std::any> tokeniseInput(std::string exprIn) {
	std::vector<std::any> tokenisedOutput = {};	// empty array of tokens to return. We're using std::any as we don't know what child class might be here
	bool isNextTokInverted = false;				// if true, next token will be a "not-ed" variable e.g. A#
	for (char c : exprIn) {						// iterate over every character in the input string
		if (countOccurrences(ALPHABET, c) > 0) {// this is a letter (i.e. a variable), so we create a variable token
			tokenisedOutput.push_back(			// add a new ParseTokenVariable, with name c (the letter), and the correct inversion
				ParseTokenVariable(
					c,
					isNextTokInverted
				)
			);
			
			isNextTokInverted = false;			// reset the inversion. This stops CA#B from making both A and C inverted (remember, the string is reversed)
		}
		else {
			if (c == '+') {						// This is an operator, create an operator token
				tokenisedOutput.push_back(
					ParseTokenOperator(c)
				);
			}
			else if (c == '#') {				// Since we are being fed a reversed string, the next variable will be inverted.
				isNextTokInverted = true;
			}
			// Any other characters will be invalid and caught by the input validation at the start of the process.
		}
	}
	// return the list of tokens we generated.
	return tokenisedOutput;
}

const char* simplifyBooleanExpr(const char* boolExprIn) {
	/* Process:
		1. The string has # after a variable to indicate that it is inverted (i.e. Not A = A#). However, it is
		much easier to process if the # comes before. Therefore, the string is reversed.

		2. The string is split into tokens, which come in a variable or operator form. These are easier to process
		and make computation simpler. It also allows for input validation.

		3. The tokens are grouped into terms which removes the + seperator in favour of a list. This is the last processing 
		step before the identities can be applied, and it serves to make it easier to search each term for the characteristics of
		each identity.

		4. identities are applied

		5. data returned
	*/

	static std::string output = "";
	output.erase(output.begin(), output.end());				// we need to return a static string, but if this has been called before output will already have a value.
					
	static std::string errorReturnString;					// as above, but this string is used if we have an error during the process
	errorReturnString.erase(errorReturnString.begin(), errorReturnString.end());	// erase the contents of the string to ensure it's empty

	// This regex checks if the input expression is in SOP format. For an explanation of how this regex works, see the design section.
	std::regex inputValidator("((([A-Z]+[#]?)+)[+]?)*[#,A-Z]$");
	std::smatch regexOutput;

	std::string boolExprInString = boolExprIn;				// we have to convert explicity from const char * to std::string

	if (!std::regex_match(boolExprInString, regexOutput, inputValidator)) {	// The input string doesn't match the validation regex
		errorReturnString = ("0@@0@@Input string |" + boolExprInString + "| is not valid."); // generate the debug error message
		return { errorReturnString.c_str()};	// stop execution and return error
	}
	
	std::string reversedExpr = reverseString(boolExprIn);
	std::vector<std::any> tokenisedExpr = tokeniseInput(reversedExpr);
	
	std::vector<ParseTokenVariable> termCollection = {};		// used to store a list of all tokens in each term as we generate the term 
	std::priority_queue<ParseTerm> termOrganisingQueue = {};	// priority queue used to organise the terms ready for simplifying
	
	std::vector<ParseTerm> identityQueue = {};				// list of terms waiting to be processed
	std::string identityDebugString = "";					// debug output for user
	int identityPassesCompleted = 0;						// amount of simplifacation rounds we have done

	output = "1@@";											// just a quirk of static strings means that it's easier to assume its all gone correctly and then say otherwise
	
	
	for (std::any tok : tokenisedExpr) {					// for every token in the tokenised expression, repeat this

		try {												// try to convert the token into a ParseTokenVariable
															// if this works, the term is a variable
			ParseTokenVariable tokVar = std::any_cast<ParseTokenVariable>(tok);
			termCollection.push_back(tokVar);				// This is a variable, add into the queue
		}
		catch (std::bad_any_cast) {							// trying to make the term a variable didn't work, so see if it's an operator instead.
			try {
				ParseTokenOperator tokOp = std::any_cast<ParseTokenOperator>(tok);
				// the term is an operator, so this is the end of the term
				if (tokOp.getData() == "+") {
					// add this term into the queue, which will be organised by its length automatically
					// the list of ParseTokenVariables is created as the data for the parse term
					termOrganisingQueue.push(
						ParseTerm(termCollection)
					);
					// reset the collection for the next term
					termCollection = {};
				}
			}
			catch (std::bad_any_cast) {
				// Something has gone _very_ wrong to get here - the term was neither variable nor operator
				// This means the input has been corrupted.
				std::string errorLog = "NULL@@0@@Tokens not generated correctly!" + std::string(boolExprIn) ;

				for (auto& errorTok : tokenisedExpr) {
					int i = (int)&errorTok;
					errorLog += "TokGEN: " + std::any_cast<ParseToken>(errorTok).getData() + std::to_string(i);
				}
				errorLog += "TokGEN - TokMG: " + std::any_cast<ParseToken>(tok).getData();
				const char* returner = errorLog.c_str();

				return { returner };
			}
		}
	}
	if (termCollection.size() > 0){			// if this term is non-empty
		termOrganisingQueue.push(			// create a new ParseTerm and add it to the prioity queue
			ParseTerm(termCollection)
		);
	}
	

	// this loop serves to remove the prioritised nature of the elements, changing the priority queue to a list
	while (!termOrganisingQueue.empty()) { // while there are still more terms to remove from the queue and place in the vector
		identityQueue.push_back(termOrganisingQueue.top()); // get the top term of the queue and add it to the list
		termOrganisingQueue.pop();							// remove the top term of the queue
	}
	
	std::vector<ParseTerm> result = applyBooleanIdentities(identityQueue, identityDebugString, identityPassesCompleted);
	

	for (ParseTerm &term : result) {
		output += term.getString();
		output += "+";
	}
	output.pop_back();
	
	if (output=="1@@") {		// if the size of the output is 0, then the output isn't dependant on any of the variables -> output is always 1
		output = "1@@1";
			// 1@@" + identityDebugString + "@@" + std::to_string(identityPassesCompleted)); // add the debug info to the string (since we have successfully got to here)
	}
	output += ("@@" + identityDebugString + "@@" + std::to_string(identityPassesCompleted)); // add the debug info to the string (since we have successfully got to here)
	
	return output.c_str(); 
}
