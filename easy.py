import sqlite3

class SQL:
    def __init__(self, path):
        self.path = path
    
    def run(self, query, params=None):
        with sqlite3.connect(self.path) as con:
            con.execute("PRAGMA foreign_keys = ON")
            
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = [dict(row) for row in cur.fetchall()]
                
                if len(results) == 1:
                    return results[0]
                else:
                    return results
            else:
                con.commit()
                return cur.rowcount

def test(actual_output, expected_output, test_name=None, tolerance=0.0001):
    is_numeric = isinstance(actual_output, (int, float)) and isinstance(expected_output, (int, float))
    
    if is_numeric and isinstance(expected_output, float):
        passed = abs(actual_output - expected_output) <= tolerance
    else:
        passed = actual_output == expected_output
    
    if passed:
        if test_name:
            print(f"✓ PASS: {test_name}")
        else:
            print(f"✓ PASS")
        return True
    else:
        if test_name:
            print(f"✗ FAIL: {test_name}")
        else:
            print(f"✗ FAIL")
        print(f"  Expected: {expected_output}")
        print(f"  Got:      {actual_output}")
        return False