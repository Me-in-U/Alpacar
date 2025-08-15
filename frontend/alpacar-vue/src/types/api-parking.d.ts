// src/types/api-parking.d.ts

declare module "@/api/parking" {
  import type { AxiosInstance } from "axios";
  export const apiClient: AxiosInstance;
  export const parkingAPI: any;
  export default parkingAPI;
}

declare module "@/api/parking.js" {
  export * from "@/api/parking";
  export { default } from "@/api/parking";
}