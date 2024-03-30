import { getAccessToken } from "./utils/getAccessToken";
import { redirectToAuthCodeFlow } from "./utils/redirectToAuthCodeFlow";
import { UserProfile } from "./interfaces"

const clientId = "9bef3c4aa58f4cf781386c814edd0cc3";
const params = new URLSearchParams(window.location.search);
const code = params.get("code");
let accessToken = sessionStorage.getItem("access-token")
const url = new URL(window.location.href)
const baseUrl = url.origin + url.pathname

onLoad()
async function onLoad() {
  getLocation()
  alert("The app is currently in beta testing mode, so if you haven't been added use the guest login")

  const submitBtn = document.getElementById("submit") as HTMLInputElement
  submitBtn!.addEventListener("click", handleSubmit)

  document.getElementById("login")!.addEventListener("click", () => redirectToAuthCodeFlow(clientId, baseUrl))
  document.getElementById("anonymous-login")!.addEventListener("click", () => { submitBtn.disabled = false; populateProfileView() })

  if (code) {
    accessToken = await getAccessToken(clientId, code, baseUrl);
    sessionStorage.setItem("access-token", accessToken)
  }
  if (accessToken) {
    const profile = await fetchProfile(accessToken);

    submitBtn.disabled = false
    populateProfileView(profile);
  }
}


async function handleSubmit(event: MouseEvent) {
  event.preventDefault()
  const recommendationsSection = document.getElementById("recommendations")
  recommendationsSection!.innerHTML = `<article aria-busy="true"></article>`

  const form = document.getElementById("input") as HTMLFormElement
  const formData = new FormData(form)
  const latitude = formData.get("latitude")?.slice(0, -1) as string
  const longitude = formData.get("longitude")?.slice(0, -1) as string
  const genres: string[] = (formData.get("genres") as string).split(",").map(entry => entry.trim())

  const template = await getRecommendations(accessToken!, latitude, longitude, genres)
  recommendationsSection!.innerHTML = template
}

async function fetchProfile(token: string): Promise<UserProfile> {
  const result = await fetch("https://api.spotify.com/v1/me", {
    method: "GET", headers: { Authorization: `Bearer ${token}` }
  });

  return await result.json();
}

function populateProfileView(profile?: UserProfile) {
  const profileSection = document.getElementById("profile")!
  const displayNameTemplate = (name: string) => `<span style="color: gray"> Logged in as </span> <span>${name}</span>`

  if (!profile) {
    profileSection.innerHTML = `<h2>${displayNameTemplate("guest")}</h2>`
    return
  }

  const profileDisplayNameTemplate = displayNameTemplate(profile.display_name)
  const profileImageTemplate = profile.images[0] ? `<img src="${profile.images[0].url}" style="border-radius: 50%; margin-left: 10px" width="50" height="50"/>` : ""
  profileSection.innerHTML = `<h2>${profileDisplayNameTemplate}${profileImageTemplate}</h2>`
}

async function getRecommendations(accessToken: string, latitude: string, longitude: string, genres: string[]) {
  const params = {
    latitude: latitude,
    longitude: longitude,
    genres: genres.join(",")
  }
  // NOTE: this could be achieved using geocoding api from OpenWeather
  const serverUrl = new URL(`${baseUrl}api/weather_recommendations`)
  serverUrl.search = new URLSearchParams(params).toString()
  const response = await fetch(serverUrl, { headers: { "Access-Token": accessToken } })
  return await response.text()
}

function getLocation() {
  const latitudeBox = document.getElementById("latitude") as HTMLInputElement
  const longitudeBox = document.getElementById("longitude") as HTMLInputElement
  navigator.geolocation.getCurrentPosition(position => {
    latitudeBox.value = position.coords.latitude + "°"
    longitudeBox.value = position.coords.longitude + "°"
  });
}
