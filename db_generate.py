from db_funcs import *
from constants import *


db_conn = DBManager()
db_conn.drop_table(table_name=S_TRIGGER_TABLE)
db_conn.drop_table(table_name=S_TRIGGER_EVENTS_TABLE)

print(f"\n==================== Creating Table :[{S_TRIGGER_TABLE}] =====================")
db_conn.create_table(table_name=S_TRIGGER_TABLE)
db_conn.add_field(table_name=S_TRIGGER_TABLE, field_name="status", field_type="VARCHAR(8)", constraints="DEFAULT 'active'")
db_conn.add_field(table_name=S_TRIGGER_TABLE, field_name="trigger_time", field_type="TIMESTAMP", constraints=S_NOT_NULL)
db_conn.add_field(table_name=S_TRIGGER_TABLE, field_name="interval", field_type="INTEGER")
db_conn.add_field(table_name=S_TRIGGER_TABLE, field_name="trigger_name", field_type="VARCHAR(100)")
db_conn.add_field(table_name=S_TRIGGER_TABLE, field_name="trigger_message", field_type="VARCHAR(100)")
db_conn.add_field(table_name=S_TRIGGER_TABLE, field_name="trigger_type", field_type="VARCHAR(20)")
db_conn.add_field(table_name=S_TRIGGER_TABLE, field_name="last_triggered_on", field_type="TIMESTAMP")
db_conn.add_field(table_name=S_TRIGGER_TABLE, field_name="trigger_count", field_type="INTEGER",constraints="DEFAULT 0")
db_conn.add_field(table_name=S_TRIGGER_TABLE, field_name="api_payload", field_type="JSONB")


print(f"\n==================== Creating Table :[{S_TRIGGER_EVENTS_TABLE}] =====================")
db_conn.create_table(table_name=S_TRIGGER_EVENTS_TABLE)
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="status", field_type="VARCHAR(30)", constraints="DEFAULT 'active'")
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="trigger_id", field_type="INTEGER", constraints=S_NOT_NULL)
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="triggered_at", field_type="TIMESTAMP", constraints=S_NOT_NULL)
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="trigger_name", field_type="VARCHAR(100)")
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="interval", field_type="INTEGER")
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="trigger_message", field_type="VARCHAR(100)")
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="trigger_type", field_type="VARCHAR(20)")
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="api_payload", field_type="JSONB")
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="archived_at", field_type="TIMESTAMP", constraints="DEFAULT (CURRENT_TIMESTAMP + INTERVAL '2 hours')")
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="deleted_at", field_type="TIMESTAMP", constraints="DEFAULT (CURRENT_TIMESTAMP + INTERVAL '48 hours')")
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="last_triggered_on", field_type="TIMESTAMP")
db_conn.add_field(table_name=S_TRIGGER_EVENTS_TABLE, field_name="trigger_count", field_type="INTEGER",constraints="DEFAULT 0")
db_conn.add_foreign_key(table_name=S_TRIGGER_EVENTS_TABLE, field_name="trigger_id", ref_table=S_TRIGGER_TABLE, ref_field="id")

