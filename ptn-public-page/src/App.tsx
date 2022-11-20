import React from 'react'
import './App.css'
import Button from '@mui/material/Button'
import Stack from '@mui/material/Stack'
import DoneIcon from '@mui/icons-material/Done'
import LoginIcon from '@mui/icons-material/Login'


function App() {
    const oauthClientId: string = process.env.REACT_APP_NOTION_OAUTH_CLIENT_ID || ''
    const oauthHandlerURI: string = process.env.REACT_APP_NOTION_OAUTH_REDIRECT_URI || ''
    const state = JSON.stringify({
        return_url: process.env.PUBLIC_URL
    })
    const authorizeUrl = `https://api.notion.com/v1/oauth/authorize?client_id=${encodeURIComponent(oauthClientId)}&response_type=code&owner=user&redirect_uri=${encodeURIComponent(oauthHandlerURI)}&state=${encodeURIComponent(state)}`
    const userId = new URLSearchParams(window.location.search).get('user');

  return (
    <div className="App">
      <header className="App-header">
          <Stack spacing={2}>
              <Button
                  variant="contained"
                  startIcon={<img src="/notion_logo.png" alt="notion logo" width={50}/>}
                  size="large"
                  sx={{p:4}}
                  href={authorizeUrl}
                  disabled={!!userId}
                  endIcon={(!!userId)?<DoneIcon/>:<LoginIcon/>}
              >
                  Authorize via Notion
              </Button>

              <Button
                  variant="contained"
                  startIcon={<img src="/telegram_logo.png" alt="telegram logo" width={50}/>}
                  size="large"
                  sx={{p:4}}
                  target="_blank"
                  href={`https://t.me/push_to_notion_bot?start=${userId}`}
                  disabled={!userId}
              >
                  Authorize Telegram
              </Button>

              <Button
                  variant="contained"
                  startIcon={<img src="/slack_logo.png" alt="slack logo" width={50}/>}
                  size="large"
                  sx={{p:4}}
                  disabled
              >
                  Authorize Slack (WIP)
              </Button>
          </Stack>
      </header>
    </div>
  )
}

export default App
