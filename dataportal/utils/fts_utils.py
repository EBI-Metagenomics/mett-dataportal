from django.db import connection
import logging

logger = logging.getLogger(__name__)

class FullTextSearchManager:
    def __init__(self, table_name, fields):
        self.table_name = table_name
        self.fields = fields

    def create_full_text_search_table(self):
        fields_definition = ", ".join(self.fields)
        create_table_query = f'''
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.table_name}_fts USING fts5(
                {fields_definition},
                content='{self.table_name}',
                content_rowid='id'
            );
        '''
        with connection.cursor() as cursor:
            logger.info(f"Creating FTS table with query: {create_table_query}")
            cursor.execute(create_table_query)

    def update_full_text_search(self):
        fields_selection = ", ".join(self.fields)
        update_table_query = f'''
            INSERT INTO {self.table_name}_fts(rowid, {fields_selection})
            SELECT id, {fields_selection} FROM {self.table_name};
        '''
        with connection.cursor() as cursor:
            logger.info(f"Updating FTS table with query: {update_table_query}")
            cursor.execute(update_table_query)
