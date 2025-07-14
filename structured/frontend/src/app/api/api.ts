import axios from "axios";
import { queryUrl } from "../url";

export const fetchAnswer = async (query: string) => {
	try {
		const res = await axios.post(queryUrl, { query: query });
		if (res.status == 200) {
			return { code: 200, message: res.data };
		}
	} catch (error: unknown) {
		console.log(error);
		return { code: 500, message: "Sorry, internal server error" };
	}
};
