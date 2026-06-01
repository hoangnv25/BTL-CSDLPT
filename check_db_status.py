
from sqlalchemy import text
from BE.database import SessionLocals, engines, circuit_breaker

for site, session_factory in SessionLocals.items():
    if not session_factory: continue
    try:
        session = session_factory()
        # Check packages count
        pkg_total = session.execute(text('SELECT COUNT(*) FROM packages')).scalar()
        pkg_delivered = session.execute(text("SELECT COUNT(*) FROM packages WHERE status = 'Delivered'")).scalar()
        print(f'{site.upper()}: Total={pkg_total}, Delivered={pkg_delivered}')
        
        # Check if package_sales_stats table exists and its count
        try:
            stats_count = session.execute(text('SELECT COUNT(*) FROM package_sales_stats')).scalar()
            print(f'  -> Stats table count: {stats_count}')
        except Exception:
            print(f'  -> Stats table not found or error')
            
        session.close()
    except Exception as e:
        print(f'{site.upper()}: ERROR {e}')
