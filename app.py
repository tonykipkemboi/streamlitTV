import requests
import pandas as pd
import streamlit as st
import datetime as dt


def get_videos(query: str, max_results: int, order: str, published_after: str, published_before: str) -> dict:
    """
    Get a list of videos from the YouTube Data API.

    Parameters:
        - query: The search query to use
        - max_results: The maximum number of results to return
        - order: The order in which to return the results
        - published_after: The start date for the search period (in ISO 8601 format)
        - published_before: The end date for the search period (in ISO 8601 format)

    Returns:
        A dictionary containing the raw video data
    """
    URL = "https://www.googleapis.com/youtube/v3/search"
    PARAMS = {
        "key": st.secrets['API_KEY'],
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": max_results,
        "order": order,
        "publishedAfter": published_after,
        "publishedBefore": published_before
    }
    response = requests.get(URL, params=PARAMS)
    data = response.json()
    return data


def data_to_df(data: dict) -> pd.DataFrame:
    """
    Convert raw data from the YouTube Data API to a Pandas dataframe.

    Parameters:
        - data: The raw data from the YouTube Data API

    Returns:
        A Pandas dataframe containing the video data
    """
    # Rename columns
    df = pd.json_normalize(data['items'])

    df = df.rename(columns={'id.videoId': 'video_id', 'snippet.publishedAt': 'publish_date',
                            'snippet.channelId': 'channel_id', 'snippet.title': 'title',
                            'snippet.description': 'description', 'snippet.channelTitle': 'channel_name'
                            })
    # Add links to videos
    df = df.assign(
        video_url=lambda x: "https://www.youtube.com/watch?v=" + x['video_id'])
    df = df.assign(
        channel_url=lambda x: "https://www.youtube.com/channel/" + x['channel_id'])

    # df to be downloaded as csv
    csv = df[['publish_date', 'video_url', 'title',
              'description', 'channel_name', 'channel_url']]
    return df, csv


def to_csv(df):
    return df.to_csv().encode('utf-8')


if __name__ == '__main__':
    st.title('Streamlit Content on YouTube:balloon:')
    with st.sidebar:
        st.image('streamlit-logo.png')
        # Create a form
        with st.form("search_form"):
            query = st.text_input('Enter Query', value="'Streamlit'",
                                  help="Use single quotes around your query to get results with exact term i.e. 'streamlit' ")
            max_results = st.number_input(
                "Max Results", value=50, min_value=5, max_value=50, help="Max is 50 and default is 5")
            order = st.selectbox("Order by video", [
                "date", "rating", "relevance", "title", "videoCount", "viewCount"])

            start, end = st.columns(2)
            with start:
                start_date = st.date_input(
                    "Start Date", value=dt.date(2023, 1, 1))
            with end:
                end_date = st.date_input("End Date")

            # Add a submit button to the form
            submitted = st.form_submit_button("Submit")

    if submitted:
        # Format dates as ISO 8601 strings
        start_date_iso = start_date.isoformat() + "T00:00:00Z"
        end_date_iso = end_date.isoformat() + "T23:59:59Z"

        raw_data = get_videos(query, max_results, order,
                              start_date_iso, end_date_iso)
        df, csv = data_to_df(raw_data)

        tab1, tab2 = st.tabs(['Data', 'Videos'])
        with tab1:
            # Show data
            st.subheader('Data from YouTube')
            st.dataframe(csv)

            # Download CSV
            csv_data = to_csv(csv)
            st.download_button(
                label="Download data as CSV",
                data=csv_data,
                file_name='content_data.csv',
                mime='text/csv'
            )
        with tab2:
            # Extract the video URLs from the dataframe
            with tab2:
                for i, row in df.iterrows():
                    with st.container():
                        st.video(row['video_url'])
                        st.header('Metadata')
                        st.write('CREATOR: ', row['channel_name'])
                        st.write('PUBLISH DATE: ', row['publish_date'])
