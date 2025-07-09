from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.query import BatchStatement, BatchType
from cassandra.util import uuid_from_time
import uuid
from datetime import datetime
import time
# import datetime


class CassandraDataBase:
    def __init__(self, contact_points=['127.0.0.1'], keyspace='yelp_keyspace'):
        self.cluster = None
        self.session = None
        self.contact_points = contact_points
        self.keyspace = keyspace

    def connect(self):
        try:
            self.cluster = Cluster(self.contact_points, load_balancing_policy=DCAwareRoundRobinPolicy())

            self.session = self.cluster.connect()
            print(f"Connected to Cassandra cluster.")


            create_keyspace_query = f"""
                CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
                WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
                AND durable_writes = true;
            """

            self.session.execute(create_keyspace_query)

            self.session.set_keyspace(self.keyspace)

        except Exception as e:
            print(f"Error connecting to or creating keyspace in cassandra: {e}")
            self.session = None

    def close(self):
        if self.cluster:
            self.cluster.shutdown()


    def create_tables(self):
        if not self.session:
            return

        try:
            create_restaurants_summary_table_query = f"""
                   CREATE TABLE IF NOT EXISTS restaurants_summary (
                       restaurant_id uuid PRIMARY KEY,
                       restaurant_name text,
                       average_rating float,
                       total_reviews int
                   );
               """
            self.session.execute(create_restaurants_summary_table_query)

            create_restaurant_reviews_table_query = f"""
                   CREATE TABLE IF NOT EXISTS restaurant_reviews (
                       restaurant_id uuid,
                       review_id timeuuid,
                       user_name text,
                       user_country text,
                       review_text text,
                       review_timestamp timestamp,
                       PRIMARY KEY (restaurant_id, review_id)
                   ) WITH CLUSTERING ORDER BY (review_id DESC);
               """
            self.session.execute(create_restaurant_reviews_table_query)

        except Exception as e:
            print(f"Error creating tables: {e}")

    def insert_restaurant_data(self, data_pages):
        if not self.session:
            return

        try:
            summary_insert = self.session.prepare("""
                INSERT INTO restaurants_summary (restaurant_id, restaurant_name, average_rating, total_reviews)
                VALUES (?, ?, ?, ?)
            """)

            review_insert = self.session.prepare("""
                INSERT INTO restaurant_reviews (restaurant_id, review_id, user_name, user_country, 
                                              review_text, review_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """)

            total_restaurants = 0
            total_reviews = 0

            for page in data_pages:
                for restaurant in page:

                    restaurant_id = uuid.uuid4()


                    self.session.execute(summary_insert, (
                        restaurant_id,
                        restaurant["Restaurant Name"],
                        restaurant["Restaurant Average Rating"],
                        restaurant["Restaurant Total Reviews"]
                    ))
                    total_restaurants += 1


                    batch_size = 100
                    batch = BatchStatement(batch_type=BatchType.UNLOGGED)
                    batch_count = 0

                    for review in restaurant["Reviews Info"]:

                        review_id = uuid_from_time(datetime.now())

                        batch.add(review_insert, (
                            restaurant_id,
                            review_id,
                            review["User Name"],
                            review["Country"],
                            review["Review Text"],
                            datetime.now()
                        ))
                        batch_count += 1
                        total_reviews += 1


                        if batch_count >= batch_size:
                            self.session.execute(batch)
                            batch = BatchStatement(batch_type=BatchType.UNLOGGED)
                            batch_count = 0

                    if batch_count > 0:
                        self.session.execute(batch)


        except Exception as e:
            print(f"Error inserting restaurant data: {e}")
            raise