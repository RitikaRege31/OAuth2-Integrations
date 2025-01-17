import axios from "axios";

const BASE_URL = "http://localhost:8000/integrations/hubspot";

// export const authorizeHubSpot = async (userId, orgId) => {
//   try {
//     const response = await axios.post(`${BASE_URL}/authorize`, {
//       params: { user_id: userId, org_id: orgId },
//     });
//     window.location.href = response.data.url;
//   } catch (error) {
//     console.error("Error during HubSpot authorization:", error);
//   }
// };
export const authorizeHubSpot = async (userId, orgId) => {
    try {
      const response = await axios.post(
        "http://localhost:8000/integrations/hubspot/authorize",
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
