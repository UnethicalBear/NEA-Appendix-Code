import errorLogging

# This is the class for a component retrived by either API
class BOMComponent:
    def __init__(self, distributor, mfn, mf, function, costPerUnit, unitsNeeded, circuitsOnChip):
        # distributor: which store sells this?
        # mfn (manufacturer part number): unique part number 
        # mf (manufacturer): which company makes this?
        # function: the boolean operation this part performs
        # cost per unit: the cost of one chip
        # units needed: the number of this chip needed to match the logical expression
        # circuits on chip: some chips may have multiple circuits, for example 4 and gates on a single
        # ...chip is a fairly common arrangement
        self.distributor = distributor
        self.mfn = mfn
        self.manufacturer = mf
        self.function = function
        self.circuitsOnChip = circuitsOnChip
        self.costPerUnit = costPerUnit
        self.unitsNeeded = unitsNeeded
        # total cost should only be accurate to a currency level
        self.totalCost = round(costPerUnit * unitsNeeded,2)
        # internal value: the ranking score of this component
        # ... -1 means not yet ranked
        self.__rankWeight = -1
    
    def getRankingParameters(self):
        # to rank we need to return the number of circuits on the chip and the total cost
        return [self.circuitsOnChip, self.totalCost]
    
    # Getter for the ranking score
    def getRankingScore(self):
        return self.__rankWeight
    # Setter for the ranking score
    def setRankingInfo(self, newRanking):
        self.__rankWeight = newRanking

    # Convert this class into a string for easy reading/debugging        
    def __repr__(self) -> str:
        # if not yet ranked
        if self.__rankWeight != -1:
            return f"[COMPONENT FROM {self.distributor} (Function={self.function}x{self.circuitsOnChip}, Cost: {self.totalCost}) RANK: {self.__rankWeight}]"
        # if has been ranked
        else:
            return f"[COMPONENT '{self.mfn}' FROM {self.distributor} (Function={self.function}x{self.circuitsOnChip}, Cost: {self.totalCost})]"
    
    # less than function so we can compare two components
    # compares the components based off their ranking score
    def __lt__(self, other):
        # we should only compare BOMComponents with other BOMComponents
        if isinstance(other, BOMComponent):
            # get their weights 
            s1, s2 = self.getRankingScore(), other.getRankingScore()
            # if either BOM component hasn't been ranked yet we should throw an error
            if s1 == -1 or s2 == -1:
                errorLogging.raiseGenericFatalError(60)
            # otherwise return the comparison
            return s1 < s2
        else:
            # we should only compare BOMComponents with other BOMComponents
            errorLogging.raiseGenericFatalError(61)