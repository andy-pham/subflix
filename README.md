
# Subflix

Stream any movies with subscene.com's subtitle, peerflix and VLC


## Quick Start

1. Install nodejs, npm & peerflix

    ```
    brew install node
    npm install -g peerflix
    ```

2. Install VLC

3. Download script

    ```
    wget 'https://raw.githubusercontent.com/andy-pham/subflix/master/subflix.py'
    ```

4. Open your preferred browser, find a magnet link and copy it

5. Enter this command

    ```
    python sublix.py <language> <http-or-magnet-link-or-torrent>
    ```

  Example:

  ```
  python subflix.py vietnamese "magnet:?xt=urn:btih:dc0b5ff98d23221746024eb34336b6891aecff25&dn=Her+%282013%29+720p+BrRip+x264+-+YIFY&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Ftracker.publicbt.com%3A80&tr=udp%3A%2F%2Ftracker.istole.it%3A6969&tr=udp%3A%2F%2Fopen.demonii.com%3A1337"
  ```

6. Enjoy :)
