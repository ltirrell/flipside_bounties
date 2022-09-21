WITH updated_metadata AS (
    SELECT
        CASE
            WHEN player = 'N/A' THEN team
            ELSE player
        END AS "Player",
        team AS "Team",
        CASE
            WHEN moment_stats_full ['metadata'] ['playerPosition'] = '' THEN 'Team'
            ELSE moment_stats_full ['metadata'] ['playerPosition']
        END AS "Position",
        season AS "Season",
        week AS "Week",
        play_type AS "Play_Type",
        moment_date AS "Moment_Date",
        moment_tier AS "Moment_Tier",
        nflallday_id AS "NFLALLDAY_ID",
        serial_number AS "Serial_Number",
        moment_stats_full ['metadata'] ['awayTeamName'] AS "Away_Team_Name",
        moment_stats_full ['metadata'] ['awayTeamScore'] AS "Away_Team_Score",
        moment_stats_full ['metadata'] ['gameDistance'] AS "Distance",
        moment_stats_full ['metadata'] ['gameDown'] AS "Down",
        moment_stats_full ['metadata'] ['gameNflID'] AS "NFL_ID",
        moment_stats_full ['metadata'] ['gameQuarter'] AS "Quarter",
        moment_stats_full ['metadata'] ['gameTime'] AS "Time",
        moment_stats_full ['metadata'] ['homeTeamName'] AS "Home_Team_Name",
        moment_stats_full ['metadata'] ['homeTeamScore'] AS "Home_Team_Score",
        moment_stats_full ['metadata'] ['playerBirthdate'] AS "Birthdate",
        moment_stats_full ['metadata'] ['playerBirthplace'] AS "Birthplace",
        moment_stats_full ['metadata'] ['playerCollege'] AS "College",
        moment_stats_full ['metadata'] ['playerDraftNumber'] AS "Draft_Number",
        moment_stats_full ['metadata'] ['playerDraftRound'] AS "Draft_Round",
        moment_stats_full ['metadata'] ['playerDraftTeam'] AS "Draft_Team",
        moment_stats_full ['metadata'] ['playerDraftYear'] AS "Draft_Year",
        moment_stats_full ['metadata'] ['playerHeight'] AS "Height",
        moment_stats_full ['metadata'] ['playerRookieYear'] AS "Rookie_Year",
        moment_stats_full ['metadata'] ['playerWeight'] AS "Weight",
        moment_stats_full ['metadata'] ['images'] [0] ['url'] AS "image",
        classification AS "Classification",
        total_circulation AS "Total_Circulation",
        moment_description AS "Moment_Description",
        nft_id AS "NFT_ID",
        series AS "Series",
        set_name AS "Set_Name",
        -- video_urls as "Video_URLs",
        CONCAT(
            'https://assets.nflallday.com/editions/',
            LOWER(REPLACE(set_name, ' ', '_')),
            '/',
            moment_stats_full ['id'],
            '/play_',
            moment_stats_full ['id'],
            '_',
            LOWER(REPLACE(set_name, ' ', '_')),
            '_capture_AnimationCapture_Video_Square_Grey_1080_1080_Grey.mp4'
        ) AS nflallday_assets_url
    FROM
        flow.core.dim_allday_metadata
),
sales_with_metadata AS (
    SELECT
        CONVERT_TIMEZONE(
            'UTC',
            'America/New_York',
            s.block_timestamp :: timestamp_ntz
        ) AS "Datetime",
        "Datetime" :: DATE AS "Date",
        s.tx_id AS "tx_id",
        s.price AS "Price",
        -- s.currency,
        s.buyer AS "Buyer",
        s.seller AS "Seller",
        -- s.counterparties,
        -- s.marketplace,
        m.*
    FROM
        flow.core.ez_nft_sales s
        INNER JOIN updated_metadata m
        ON m.nft_id = s.nft_id
    WHERE
        s.nft_collection = 'A.e4cf4bdc1751c65d.AllDay'
        AND s.tx_succeeded = 'True'
)
SELECT
    *
FROM
    sales_with_metadata
WHERE
    "Team" = {{ team }}
