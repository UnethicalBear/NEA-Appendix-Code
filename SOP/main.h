#pragma once

#ifdef SOP_EXPORTS
#define SOP_API __declspec(dllexport)
#else
#define SOP_API __declspec(dllimport)
#endif

extern "C" SOP_API const char* sumOfProducts(const char* truthTable, const int rowWidth);
//extern SOP_API const char* _sumOfProducts(std::vector<std::vector<bool>> truthTable);
// This defines the function to the compiler so that it can be exported to a dll. 


extern "C" SOP_API const char * simplifyBooleanExpr(const char * boolExprIn);
// This defines the function to the compiler so that it can be exported to a dll. 
