'use client'
import { useState, useEffect, useRef } from "react";
import { fetchAnswer } from "../api/api";
import { toast } from "react-toastify";
import ReactMarkdown from "react-markdown";

type Message = {
    role: 'user' | 'assistant';
    content: string;
}


export default function Chatbox() {
    const [userInputValue, setUserInputValue] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const chatRef = useRef(null);

    useEffect(() => {
        if (chatRef.current) {
            chatRef.current.scrollTop = chatRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setUserInputValue("");

        setMessages(prevMessages => [...prevMessages, { role: 'user', content: userInputValue }]);
        setMessages(prevMessages => [...prevMessages, { role: 'assistant', content: '' }]);
        setIsStreaming(true);

        const userQuery = e.target.message.value
        const res = await fetchAnswer(userQuery)
        if (res?.code == 200) {
            const answer = res.message.answer
            setMessages(prev => {
                const allMessages = [...prev];
                allMessages[allMessages.length - 1].content = answer;
                return allMessages;
            })
        } else {
            toast(res?.message)
        }
        setIsStreaming(false);

        //
        // const response = await fetchStreamingApi("query", {
        //     method: "POST",
        //     body: JSON.stringify({"query": e.target.message.value, "file_path": file_path}),
        // });

        // const reader = response.body.getReader();
        // const decoder = new TextDecoder();
        // let assistantMessage = '';
        //
        // while (true) {
        //     const { value, done } = await reader.read();
        //     if (done) break;
        //     
        //     const chunk = decoder.decode(value);
        //     const lines = chunk.split('\n');
        //
        //     for (const line of lines) {
        //         if (line.startsWith('data: ')) {
        //             const data = line.slice(6);
        //             if (data === '[DONE]') {
        //                 setIsStreaming(false);
        //                 break;
        //             }
        //             
        //             try {
        //                 const parsed = JSON.parse(data);
        //                 assistantMessage += parsed.content;
        //                 
        //                 setMessages(prev => {
        //                     const newMessages = [...prev];
        //                     newMessages[newMessages.length - 1].content = assistantMessage;
        //                     return newMessages;
        //                 });
        //             } catch (e) {
        //                 console.error('Error parsing JSON:', e);
        //             }
        //         }
        //     }
        // }

    }


    return (
        <div className="w-[50%] p-2 border-2 border-gray-300 rounded-md bg-gray-900">
            <div ref={chatRef} className="w-full h-[calc(100%-50px)] py-1 mb-2 flex flex-col gap-2 text-sm overflow-y-auto no-scrollbar">
                {messages.map((message, index) => (
                    <div key={index} className={`max-w-[80%] ${message.role === 'user' ? 'bg-gray-200 rounded-sm p-1 px-2 ml-auto mt-0 text-black' : 'bg-blue-500 rounded-sm p-1 px-2 mr-auto mt-0 text-white'}`}>
                        <ReactMarkdown>
                            {message.content}
                        </ReactMarkdown>
                        {isStreaming && index === messages.length - 1 && (
                            <span className="inline-block w-1 h-4 ml-1 bg-white animate-pulse" />
                        )}
                    </div>
                ))}
            </div>
            <form onSubmit={handleSubmit} className="w-full h-10 border-2 border-gray-300 rounded-md bg-gray-900">
                <input
                    name="message"
                    type="text"
                    className="w-full h-full p-3"
                    placeholder={isStreaming ? "Thinking..." : "Ask me about the paper"}
                    onChange={(e) => setUserInputValue(e.target.value)}
                    value={userInputValue}
                    disabled={isStreaming}
                />
            </form>
        </div>
    )
}
