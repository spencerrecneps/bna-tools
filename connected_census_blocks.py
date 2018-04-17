import psycopg2
import yaml
from tqdm import tqdm
import psycopg2
from psycopg2 import sql

config = yaml.safe_load(open("project_setup.yaml"))

host = config["db"]["host"]
db = config["db"]["dbname"]
user = config["db"]["user"]
password = config["db"]["password"]
db_connection_string = " ".join([
    "dbname=" + db,
    "user=" + user,
    "host=" + host,
    "password=" + password
])
conn = psycopg2.connect(db_connection_string)

cur = conn.cursor()

# cur.execute('truncate neighborhood_connected_census_blocks')
# conn.commit()

cur.execute(' \
    select blockid10 from neighborhood_census_blocks cb, neighborhood_boundary b \
    where st_intersects(cb.geom,b.geom) \
    and not exists (select 1 from generated.neighborhood_connected_census_blocks c \
        where c.source_blockid10 = cb.blockid10 \
    ) \
')

for b in tqdm(cur.fetchall()):
    q = sql.SQL(" \
        INSERT INTO generated.neighborhood_connected_census_blocks ( \
            source_blockid10, target_blockid10, \
            low_stress, low_stress_cost, high_stress, high_stress_cost \
        ) \
        SELECT  source.blockid10, \
                target.blockid10, \
                FALSE, \
                ( \
                    SELECT  MIN(ls.total_cost) \
                    FROM    neighborhood_reachable_roads_low_stress ls \
                    WHERE   ls.base_road = ANY(source.road_ids) \
                    AND     ls.target_road = ANY(target.road_ids) \
                ), \
                TRUE, \
                ( \
                    SELECT  MIN(hs.total_cost) \
                    FROM    neighborhood_reachable_roads_low_stress hs \
                    WHERE   hs.base_road = ANY(source.road_ids) \
                    AND     hs.target_road = ANY(target.road_ids) \
                ) \
        FROM    neighborhood_census_blocks source, \
                neighborhood_census_blocks target \
        WHERE   source.blockid10 = {} \
        AND     ST_DWithin(source.geom,target.geom,2680); \
    ").format(
        sql.Literal(b)
    )
    # print(q.as_string(conn))
    cur.execute(q)
    conn.commit()

cur.execute(" \
    UPDATE  generated.neighborhood_connected_census_blocks \
    SET     low_stress = TRUE \
    WHERE   EXISTS ( \
                SELECT  1 \
                FROM    neighborhood_census_blocks source, \
                        neighborhood_census_blocks target \
                WHERE   neighborhood_connected_census_blocks.source_blockid10 = source.blockid10 \
                AND     neighborhood_connected_census_blocks.target_blockid10 = target.blockid10 \
                AND     source.road_ids && target.road_ids \
            ) \
    OR      ( \
                low_stress_cost IS NOT NULL \
            AND CASE    WHEN COALESCE(high_stress_cost,0) = 0 THEN TRUE \
                        ELSE low_stress_cost::FLOAT / high_stress_cost <= 1.25 \
                        END \
            ); \
 ")

conn.commit()

 cur.execute(" \
    CREATE UNIQUE INDEX idx_neighborhood_blockpairs ON neighborhood_connected_census_blocks (source_blockid10,target_blockid10); \
    CREATE INDEX IF NOT EXISTS idx_neighborhood_blockpairs_lstress ON neighborhood_connected_census_blocks (low_stress) WHERE low_stress IS TRUE; \
    CREATE INDEX IF NOT EXISTS idx_neighborhood_blockpairs_hstress ON neighborhood_connected_census_blocks (high_stress) WHERE high_stress IS TRUE; \
    ANALYZE neighborhood_connected_census_blocks; \
")

conn.commit()
