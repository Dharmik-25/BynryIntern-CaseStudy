from flask import request, jsonify, Blueprint
from app.models import db, Product, Inventory, Warehouse, Supplier, product_suppliers, func
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime, timedelta
import math

# --- Part 1: create_product endpoint ---
@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    required_fields = ['name', 'sku', 'price', 'warehouse_id']
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({'error': f'{field} is required and cannot be empty'}), 400
    
    quantity = int(data.get('initial_quantity', 0)) if data.get('initial_quantity') else 0
    
    warehouse = Warehouse.query.get(data['warehouse_id'])
    if not warehouse:
        return jsonify({'error': 'Warehouse does not exist'}), 404
    
    if Product.query.filter_by(sku=data['sku'].strip()).first():
        return jsonify({'error': 'SKU already exists'}), 400
    
    try:
        product = Product(name=data['name'].strip(), sku=data['sku'].strip(), price=Decimal(str(data['price'])))
        db.session.add(product)
        db.session.flush()
        
        existing_inventory = Inventory.query.filter_by(product_id=product.id, warehouse_id=data['warehouse_id']).first()
        if existing_inventory:
            existing_inventory.quantity += quantity
        else:
            inventory = Inventory(product_id=product.id, warehouse_id=data['warehouse_id'], quantity=quantity)
            db.session.add(inventory)
        
        db.session.commit()
        return jsonify({'message': 'Product created', 'product_id': product.id}), 201
    except IntegrityError as ie:
        db.session.rollback()
        return jsonify({'error': 'Database error, try again'}), 500
    except ValueError as ve:
        db.session.rollback()
        return jsonify({'error': 'Invalid price or quantity'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Unexpected issue: {str(e)}'}), 500

# --- Part 3: low_stock_alerts endpoint ---
bp = Blueprint('alerts', __name__)

@bp.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def low_stock_alerts(company_id):
    recent_period = datetime.utcnow() - timedelta(days=30)
    
    alerts = []
    query = db.session.query(Inventory, Product, Warehouse, Supplier)\
        .join(Product, Inventory.product_id == Product.id)\
        .join(Warehouse, Inventory.warehouse_id == Warehouse.id)\
        .join(product_suppliers, Product.id == product_suppliers.c.product_id)\
        .join(Supplier, product_suppliers.c.supplier_id == Supplier.id)\
        .filter(Warehouse.company_id == company_id)
    
    for inv, prod, wh, supp in query.all():
        threshold = prod.low_stock_threshold if prod.low_stock_threshold else 20
        if inv.quantity < threshold:
            if inv.last_updated >= recent_period:
                recent_changes = db.session.query(func.sum(inventory_changes.change_quantity))\
                    .join(inventory, inventory_changes.product_id == inv.product_id)\
                    .filter(inventory_changes.change_date >= recent_period).scalar() or 0
                avg_daily_use = abs(recent_changes) / 30 if recent_changes else 1
                days_left = math.floor(inv.quantity / avg_daily_use) if avg_daily_use > 0 else 0
                
                alert = {
                    "product_id": prod.id,
                    "product_name": prod.name,
                    "sku": prod.sku,
                    "warehouse_id": wh.id,
                    "warehouse_name": wh.name,
                    "current_stock": inv.quantity,
                    "threshold": threshold,
                    "days_until_stockout": days_left,
                    "supplier": {
                        "id": supp.id,
                        "name": supp.name,
                        "contact_email": supp.contact_email
                    }
                }
                alerts.append(alert)
    
    return jsonify({"alerts": alerts, "total_alerts": len(alerts)}), 200
