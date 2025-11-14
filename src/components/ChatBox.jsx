import {
  VStack,
  HStack,
  Heading,
  Input,
  Box,
  InputGroup,
  InputRightElement,
  Button,
  Container,
  Text
} from "@chakra-ui/react";
import { TbArrowRight } from "react-icons/tb";
import ChatMessage from "./ChatMessage";

import { AnimatePresence } from "framer-motion";
import { useState } from "react";

import { useEffect, useRef } from "react";

function ChatBox({ messages, setMessages, sessionId,initialMessage }) {
  
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const didSendFirstMessage = useRef(false);


  const sendMessage = async (inputFallback) => {
    if (isStreaming) return;

    setIsStreaming(true);  
    const userMessageText = (inputFallback != undefined) ? inputFallback : input;

    if(!userMessageText.trim()){
      setIsStreaming(false);
      return
    }

    const userMessage = {text: userMessageText, isUser: true};
    setInput("");

    setMessages((prev) => [
      ...prev, userMessage, {text:"", isUser: false}
    ]);

    const response = await fetch("/api/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessageText,
        sessionId: sessionId, 
      }),
    });
    
   console.log(response.body)

    if(!response.body){
      
      return
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while(true){
      const {done, value} = await reader.read();
      if(done){
        break
      }

      const token = decoder.decode(value) + " ";
      console.log(token)

      setMessages((prevMessages) => {
        const allButLast = prevMessages.slice(0, -1);
        const lastMessage = prevMessages[prevMessages.length - 1];

        return [...allButLast,{
          ...lastMessage, text: lastMessage.text + token
        }]
      })
    }

    console.log(messages)
    setIsStreaming(false);

  }

  useEffect(() => {
    if (initialMessage && !didSendFirstMessage.current) {
      didSendFirstMessage.current = true; 
      sendMessage(initialMessage); 
    }
  }, [initialMessage]);

  useEffect(() => {
    const chatBoxContainer = document.getElementById("chatBoxContainer");

    if (chatBoxContainer) {
      chatBoxContainer.scrollTo({
        top: chatBoxContainer.scrollHeight,
        behaviour: "smooth",
      });
    }
  }, [messages]);

  return (
    <VStack w="100%" maxW="2xl" h="60vh" p={4} spacing={0}>
      <HStack  w="100%" maxW="2xl"
      display="flex" justifyContent="space-between">
        <Box>
          <Text fontSize={18}>
            Patient
          </Text>
        </Box>
        <Box>
          <Text fontSize={18}>
            Doctor
          </Text>
        </Box>
      </HStack>
      <Box
        flex={1}
        w="2xl"
        overflowY="auto"
        bg="#e5e4dc"
        borderRadius={5}
        
        id="chatBoxContainer"
        sx={{
          "&::-webkit-scrollbar": {
            width: "8px",
          },
          "&::-webkit-scrollbar-track": {
            background: "#dcd9ce",
            borderRadius: "8px",
          },
          "&::-webkit-scrollbar-thumb": {
            background: "#b3b1a7",
            borderRadius: "8px",
          },
          "&::-webkit-scrollbar-thumb:hover": {
            background: "#8d8b84",
          },
        }}
      >
        <VStack w="100%" spacing={3} align="stretch" p={4} bg="#e5e4dc">
          <AnimatePresence initial={false}>
            {messages.map((msg, index) => (
              <ChatMessage key={index} message={msg.text} isUser={msg.isUser} isStreaming={isStreaming} />
            ))}
          </AnimatePresence>
        </VStack>
      </Box>
      <Box bg="#e5e4dc" w="2xl" p={4} mt={6}  borderRadius={5} >
      <InputGroup    >
        <Input
          placeholder="Continue the session..."
          variant="flushed"
          borderColor="gray.800"
          fontSize="lg"
          _focus={{ borderColor: "#080808", boxShadow: "none" }}
          value={input}
          fontFamily="grotesk"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key == "Enter") sendMessage();
          }}
        />
        <InputRightElement>
          <Button
            size="sm"
            h="100%"
            bg="none"
            _hover={{ bg: "transparent" }}
            px={3}
            fontSize={20}
            onClick={sendMessage}
          >
            <TbArrowRight />
          </Button>
        </InputRightElement>
      </InputGroup>
      </Box>
    </VStack>
  );
}

export default ChatBox;
