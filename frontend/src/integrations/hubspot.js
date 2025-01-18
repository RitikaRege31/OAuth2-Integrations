// import axios from "axios";

// const BASE_URL = "http://localhost:8000/integrations/hubspot";

// export const authorizeHubSpot = async (userId, orgId) => {
//     try {
//       const response = await axios.post(
//         "http://localhost:8000/integrations/hubspot/authorize",
//         new URLSearchParams({
//           user_id: userId,
//           org_id: orgId,
//         })
//       );
//       window.location.href = response.data.url;
//     } catch (error) {
//       console.error("Error during HubSpot authorization:", error);
//     }
//   };
  

// export const getHubSpotItems = async (userId, orgId) => {
//   try {
//     const response = await axios.get(`${BASE_URL}/items`, {
//       params: { user_id: userId, org_id: orgId },
//     });
//     return response.data.items;
//   } catch (error) {
//     console.error("Error fetching HubSpot items:", error);
//     return [];
//   }
// };
import React, { useState } from 'react';
import axios from 'axios';

const BASE_URL = "http://localhost:8000/integrations/hubspot";

// Function to handle HubSpot authorization
export const authorizeHubSpot = async (userId, orgId) => {
  try {
    const response = await axios.post(
      `${BASE_URL}/authorize`,
      new URLSearchParams({
        user_id: userId,
        org_id: orgId,
      })
    );
    window.location.href = response.data.url;
  } catch (error) {
    console.error("Error during HubSpot authorization:", error);
  }
};

// Function to fetch HubSpot items
export const getHubSpotItems = async (userId, orgId) => {
  try {
    const response = await axios.get(`${BASE_URL}/items`, {
      params: { user_id: userId, org_id: orgId },
    });
    return response.data.items;
  } catch (error) {
    console.error("Error fetching HubSpot items:", error);
    return [];
  }
};

// HubSpot OAuth Integration Component
const HubSpotAuth = () => {
  const [authUrl, setAuthUrl] = useState('');
  const [tokens, setTokens] = useState(null);
  const [userId, setUserId] = useState('');

  // Update with your actual HubSpot OAuth credentials
  const HUBSPOT_CLIENT_ID = '0252423f-9a2d-4434-b622-3b2129f9c46d';
  const HUBSPOT_REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback';

  // Updated authorization URL with the required scope
//   const authorization_url = (
//     `https://app.hubspot.com/oauth/authorize?` +
//     `client_id=${HUBSPOT_CLIENT_ID}&redirect_uri=${HUBSPOT_REDIRECT_URI}&` +
//     `scope=crm.objects.contacts.read%20crm.objects.contacts.write`
//   );
const authorization_url = (
    `https://app.hubspot.com/oauth/authorize?client_id=0252423f-9a2d-4434-b622-3b2129f9c46d&redirect_uri=http://localhost:8000/integrations/hubspot/oauth2callback&scope=crm.objects.contacts.write%20oauth%20crm.objects.companies.write%20crm.lists.write%20crm.objects.companies.read%20crm.lists.read%20crm.objects.contacts.&state={user_id}` 
);
  

  const REDIS_BACKEND_URL = 'http://localhost:8000'; // Change to your backend URL

  // Step 1: Get HubSpot OAuth authorization URL
  const getAuthUrl = () => {
    setAuthUrl(authorization_url);
  };

  // Step 2: Handle OAuth callback and exchange code for tokens
  const handleOAuthCallback = async (code) => {
    try {
      // Call your backend API to exchange the code for tokens
      const response = await axios.get(`${REDIS_BACKEND_URL}/oauth2callback?code=${code}&user_id=${userId}`);
      const tokens = response.data.tokens;

      // Save tokens to the state
      setTokens(tokens);

      // Store tokens in the backend (Redis)
      await saveTokens(userId, tokens);

      alert('OAuth successful, tokens saved!');
    } catch (error) {
      console.error('Error during OAuth callback:', error);
      alert('Error during OAuth callback!');
    }
  };

  // Step 3: Save tokens to the backend (Redis)
  const saveTokens = async (userId, tokens) => {
    try {
      await axios.post(`${REDIS_BACKEND_URL}/save_tokens`, {
        user_id: userId,
        tokens: tokens,
      });
      alert('Tokens saved successfully in Redis!');
    } catch (error) {
      console.error('Error saving tokens:', error);
      alert('Error saving tokens!');
    }
  };

  // Step 4: Retrieve tokens from the backend (Redis)
  const retrieveTokens = async () => {
    try {
      const response = await axios.get(`${REDIS_BACKEND_URL}/get_tokens?user_id=${userId}`);
      setTokens(response.data.tokens);
      alert('Tokens retrieved from Redis!');
    } catch (error) {
      console.error('Error retrieving tokens:', error);
      alert('Error retrieving tokens!');
    }
  };

  return (
    <div>
      <h1>HubSpot OAuth Integration</h1>

      {/* Button to get OAuth URL */}
      <button onClick={getAuthUrl}>Get OAuth URL</button>
      {authUrl && (
        <div>
          <p>
            Click <a href={authUrl} target="_blank" rel="noopener noreferrer">here</a> to authorize your HubSpot account.
          </p>
        </div>
      )}

      {/* Input field for user ID (for saving/retrieving tokens) */}
      <input
        type="text"
        placeholder="Enter User ID"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
      />

      {/* Button to retrieve tokens */}
      <button onClick={retrieveTokens}>Retrieve Tokens</button>

      {/* Display retrieved tokens */}
      {tokens && (
        <div>
          <h3>Tokens:</h3>
          <pre>{JSON.stringify(tokens, null, 2)}</pre>
        </div>
      )}

      {/* OAuth callback simulation */}
      {/* Ideally, the callback will happen automatically when the user is redirected after authorization */}
      {/* For now, this button will simulate the OAuth callback with a mock authorization code */}
      <button onClick={() => handleOAuthCallback('mockAuthCode123')}>Simulate OAuth Callback</button>
    </div>
  );
};

export default HubSpotAuth;
