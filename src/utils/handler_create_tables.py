from components import do_transaction_pg
from components import setting 

def create_relevant_tables() -> dict:
    sql = f"""
        CREATE SCHEMA IF NOT EXISTS volunteer;
        

        CREATE TABLE IF NOT EXISTS volunteer.v_list
        (
            sn_excel            INT,
            org                 VARCHAR NOT NULL,
            v_id                VARCHAR NOT NULL,
            v_name              VARCHAR,
            v_character         VARCHAR,
            basin_id            VARCHAR,
            basin_name          VARCHAR,
            region              VARCHAR,
            squad               VARCHAR,
            patrol_area_id      INT,
            patrol_area_name    VARCHAR,
            note                VARCHAR,
            member              VARCHAR,
            couple_group        INT,
            year                INT, 
            CONSTRAINT v_list_pkey PRIMARY KEY (org, v_id, year)
        );


        CREATE TABLE IF NOT EXISTS volunteer.v_ingroup
        (
            group_id        VARCHAR NOT NULL,
            group_name      VARCHAR,
            org             VARCHAR,
            v_id            VARCHAR,
            user_id         VARCHAR NOT NULL,
            display_name    VARCHAR,
            picture_url     VARCHAR,
            datetime_join   timestamp without time zone,
            datetime_leave  timestamp without time zone,
            CONSTRAINT v_ingroup_pkey PRIMARY KEY (group_id, user_id)
        );


        CREATE TABLE IF NOT EXISTS volunteer.linebot_joined_groups
        (
            group_id        VARCHAR NOT NULL PRIMARY KEY,
            group_name      VARCHAR,
            datetime_join   timestamp without time zone,
            collected_msg   BOOLEAN DEFAULT false,
            note            VARCHAR
        );


        CREATE TABLE IF NOT EXISTS volunteer.v_msgs
        (
            msg_id      VARCHAR PRIMARY KEY,
            datetime    timestamp without time zone NOT NULL,
            date        date NOT NULL,
            "time"      time without time zone NOT NULL,
            session     VARCHAR,
            group_id    VARCHAR,
            user_id     VARCHAR,
            msg_type    VARCHAR, 
            content     VARCHAR
        );


        CREATE SEQUENCE IF NOT EXISTS volunteer.v_rainfall_events_id_seq;
        CREATE TABLE IF NOT EXISTS volunteer.v_rainfall_events
        (
            id              INT NOT NULL DEFAULT nextval('volunteer.v_rainfall_events_id_seq'::regclass),
            title           VARCHAR,
            datetime_record timestamp without time zone,
            status          VARCHAR,
            datetime_begin  timestamp without time zone,
            datetime_end    timestamp without time zone,
            note            VARCHAR,
            CONSTRAINT v_rainfall_events_pkey PRIMARY KEY (id)
        );

        CREATE INDEX IF NOT EXISTS v_msgs_index ON volunteer.v_msgs(datetime);
    """
    do_transaction_pg.do_transaction_command_manage(config_db=setting.config_db, sql_string=sql)
    return {
        "status": True,
        "detail": "created relevant tables already"
    }