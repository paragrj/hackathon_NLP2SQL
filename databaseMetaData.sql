-- Customers Table

CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    Name VARCHAR(100),
    Segment VARCHAR(50),
    RiskRating INT
);

-- Loans Table

CREATE TABLE Loans (
    LoanID INT PRIMARY KEY,
    CustomerID INT,
    LoanAmount DECIMAL(18, 2),
    LoanStartDate DATE,
    MaturityDate DATE,
    InterestRate DECIMAL(5, 2),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);

-- Impairments Table

CREATE TABLE Impairments (
    ImpairmentID INT PRIMARY KEY,
    LoanID INT,
    AssessmentDate DATE,
    Stage INT CHECK (Stage IN (1, 2, 3)),ex
    ExpectedCreditLoss DECIMAL(18, 2),
    ProvisionAmount DECIMAL(18, 2),
    FOREIGN KEY (LoanID) REFERENCES Loans(LoanID)
);