-- Customers Table
DROP TABLE IF EXISTS Customers;
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    Name VARCHAR(100),
    Segment VARCHAR(50),
    RiskRating INT
);

-- Loans Table
DROP TABLE IF EXISTS Loans;
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
DROP TABLE IF EXISTS Impairments;
CREATE TABLE Impairments (
    ImpairmentID INT PRIMARY KEY,
    LoanID INT,
    AssessmentDate DATE,
    Stage INT CHECK (Stage IN (1, 2, 3)),
    ExpectedCreditLoss DECIMAL(18, 2),
    ProvisionAmount DECIMAL(18, 2),
    FOREIGN KEY (LoanID) REFERENCES Loans(LoanID)
);

-- Insert sample customers
INSERT INTO Customers VALUES (1, 'Alice Corp', 'Corporate', 2);
INSERT INTO Customers VALUES (2, 'Bob Ltd', 'SME', 3);
INSERT INTO Customers VALUES (3, 'Charlie Inc', 'Retail', 4);

-- Insert sample loans
INSERT INTO Loans VALUES (1001, 1, 1000000, '2023-01-01', '2028-01-01', 5.5);
INSERT INTO Loans VALUES (1002, 2, 250000, '2022-07-01', '2025-07-01', 6.2);
INSERT INTO Loans VALUES (1003, 3, 75000, '2024-04-01', '2027-04-01', 7.0);

-- Insert sample impairments
INSERT INTO Impairments VALUES (501, 1001, '2025-04-30', 1, 5000.00, 5000.00);
INSERT INTO Impairments VALUES (502, 1002, '2025-04-30', 2, 15000.00, 12000.00);
INSERT INTO Impairments VALUES (503, 1003, '2025-04-30', 3, 30000.00, 27000.00);