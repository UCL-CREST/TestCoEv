# A Tool for establishing the test-to-code traceability link by CoEv strategy 
## 1. Description

It is a tool for establishing the test-to-code traceability link from the co-evolution relationship between the methods 
and functions in the same commit. 

## 2. Quick links

* If you want to know how to install the tool, please follows the instructions in 
[this document](/docs/install_instructions.md). 

* If you want to know the usage and example for use the tool please view 
[this link about usage with example](/docs/usages_with_example.md). 

* If you want to know more about the `test-to-code traceability link` and the `CoEv Strategy`, please go to 
[this link about the basic conception](/docs/basic_conception.md). 

* Or if you are interesting about the structure and how the tool works, please go to 
[this link about the architecture design](/docs/architecture_design.md). 

## 3. Project Structure
```
📦src
 ┣ 📂commits2sql             // The directory for codes about mining repository and then storing results into database
 ┃ ┣ 📂database                  // The classes for handling operations to a database 
 ┃ ┣ 📂modification              // The classes warpping the PyDriller and the GumTreeDiff
 ┃ ┗ 📜miner.py                  // The main class providing APIs about repository mining 
 ┣ 📂sql2link                // The directory for codes about establishing the traceability links from the database 
 ┃ ┣ 📂establisher               // The classes for the implementations of the different link establishing strategies
 ┃ ┗ 📜predictor.py              // The main class providing APIs about the links predicting
 ┣ 📂evaluator4link          // The directory for codes about evaluating the strategy
 ┃ ┣ 📂measurements              // The classes for the implementation of different measurements methods 
 ┃ ┗ 📜evaluator.py              // The main class providing APIs about the stratgy evaluating
 ┗ 📂test                    // Tests for the codes
```
