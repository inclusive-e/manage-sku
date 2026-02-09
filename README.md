# manage-sku
Manage SKU(Stock Keeping Unit) with AI enabled prediction

SKU - prediction analysis how to do that?

* Collect / Create a historical list of data to predict on - An individual user

* User journey: 
  - User can upload a csv, xls, json, pdf, image - stock, sales, inventory
  - Extract information from the uploaded file
  - Store the data into database
  - Generate a data analysis dashboard based on the stored data

* What should the data analysis dashboard show?
  - minimum 3 months of revenue and stock/inventory view
  - Predictions for future sales trends - revenue, stock, inventory
  - Inventory SKU max to min items


The Core of Manage SKU system (API first) lies around:
1. Gathering raw data
2. Pre-processing input data for NN
3. Post-processing Raw output data from NN
4. Final Output
