import React from 'react'
import './App.css'
import Button from '@mui/material/Button'
import Stack from '@mui/material/Stack'
import DoneIcon from '@mui/icons-material/Done'
import LoginIcon from '@mui/icons-material/Login'


function App() {
  const notionOauthClientId: string = process.env.REACT_APP_NOTION_OAUTH_CLIENT_ID || ''
  const notionOauthHandlerURI: string = process.env.REACT_APP_NOTION_OAUTH_REDIRECT_URI || ''
  const notionAuthState = JSON.stringify({return_url: process.env.PUBLIC_URL})
  const authorizeNotionUrl = `https://api.notion.com/v1/oauth/authorize?client_id=${encodeURIComponent(notionOauthClientId)}&response_type=code&owner=user&redirect_uri=${encodeURIComponent(notionOauthHandlerURI)}&state=${encodeURIComponent(notionAuthState)}`

  const userId = new URLSearchParams(window.location.search).get('user');
  const slackOauthClientId: string = process.env.REACT_APP_SLACK_OAUTH_CLIENT_ID || ''
  const slackOauthHandlerURI: string = process.env.REACT_APP_SLACK_OAUTH_REDIRECT_URI || ''
  const slackAuthState = JSON.stringify({return_url: process.env.PUBLIC_URL + `?user=${userId}`, user: userId})
  const authorizeSlackUrl = `https://slack.com/oauth/v2/authorize?client_id=${encodeURIComponent(slackOauthClientId)}&scope=reactions:write,chat:write,files:read,chat:write.public,commands,im:read,app_mentions:read,im:history&user_scope=identify&state=${encodeURIComponent(slackAuthState)}&redirect_uri=${encodeURIComponent(slackOauthHandlerURI)}`

  return (
    <div className="App">
      <header className="App-header">
        <Stack spacing={2}>
          <Button
            variant="contained"
            startIcon={<img src="/notion_logo.png" alt="notion logo" width={50}/>}
            size="large"
            sx={{p:4}}
            href={authorizeNotionUrl}
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
            href={authorizeSlackUrl}
            disabled={!userId}
          >
            Authorize Slack
          </Button>
        </Stack>
      </header>
    </div>
  )
}

export default App
