# Bynry Backend Engineering Intern Case Study Submission

Hi Bynry team! I’ve tried my best to build this StockFlow system. I looked through the code, made a database, and also added an alert API. The idea was to help small shops keep track of their products and suppliers. I tried to fix the missing stuff where I could, and wrote down things I wasn’t fully sure about. I made every change with the hope that it makes things easier and faster for the users.

**Dharmik Pandya**  
LinkedIn: https://linkedin.com/in/dharmikpandya25  
Date: July 23, 2025

## Part 1: Code Review & Debugging

### Issues
- No input validation for required fields (`name`, `sku`, etc.).
- SKU uniqueness not checked.
- Price uses float, risking rounding.
- Separate transactions for product and inventory.
- No warehouse validation.
- Missing `initial_quantity` handling.
- Ignores multiple warehouses.
- No error handling.
- Risk of inventory overwrite.

  
### Impact
- Crashes or bad data from missing fields.
- Duplicate SKUs confuse inventory.
- Price rounding affects margins.
- Inconsistent data from failed transactions.
- Invalid warehouse links break reports.
- KeyErrors reject partial data.
- Single-warehouse limit reduces flexibility.
- No error feedback frustrates users.
- Duplicate inventory skews counts.

  
## Part 2: Database Design 

### Gaps
How is low_stock_threshold set (per product or warehouse)?
What’s “recent sales activity” (e.g., 30 days)?
Should we track batch expiry or lot numbers?
Any supplier minimum order rules?
How are bundle prices calculated?

### Decisions Made :
Indexes on inventory fields speed up joins.
ON DELETE CASCADE cleans up data.
low_stock_threshold added for alerts.

### Assumption:
Bundles use is_bundle flag.
Impact: Supports multi-warehouse tracking and reordering.

## Part 3: Alert API

### Edge Cases
No recent sales skipped by last_updated filter.
Missing threshold defaults to 20.
No supplier excluded by join; could add a fallback.
Zero stock returns 0 days.
High load mitigated with indexes.

### Approach
Joined tables for all data, filtered by threshold and recent activity, estimated stockout with change data.
Assumption: 30-day period, 1-unit avg use if no changes.
Impact: Timely alerts reduce stockouts.
Scalability: Indexes help; pagination could be added.

### Assumptions
Warehouse model exists in app.models.
30-day recent sales period based on typical inventory cycles.
low_stock_threshold defaults to 20 if null.
Avg daily use is 1 unit if no change data.
No sales table; used last_updated as proxy.
