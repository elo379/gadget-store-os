import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "GSOS — Gadget Store OS",
    short_name: "GSOS",
    description: "Gadget Store Operating System",
    start_url: "/",
    display: "standalone",
    background_color: "#f7f7f5",
    theme_color: "#171717",
    orientation: "portrait",
  };
}
