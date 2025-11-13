//  Some Imports

import {
  Box,
  Heading,
  VStack,
  HStack,
  Input,
  IconButton,
} from "@chakra-ui/react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

import Header from "./components/Header";
import WelcomeInput from "./components/WelcomeInput";
import ChatBox from "./components/ChatBox";
import Footer from "./components/Footer";
// import DownHeading from "./components/Footer";
// import RainBackground from "./components/StarRainBackground";
import FeaturesFloating from "./components/FeaturesFloating";
// import StarRainBackground from "./components/StarRainBackground";
// import Noise from "./components/Noise";

import { v4 as uuidv4 } from 'uuid';

 
const MotionBox = motion(Box);
const MotionVStack = motion(VStack);

function App() {
  // Logic For The ChatBox Open Animation
  const [isChatOpen, setIsChatOpen] = useState(false);

  const [messages, setMessages] = useState([]);
  const [sessionID] = useState( () => uuidv4());
  const [initialMessage, setInitialMessage] = useState("");

  console.log(sessionID)



  const handleStartChat = (firstMessage) => {
   
    setInitialMessage(firstMessage);
    setIsChatOpen(true);




  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      h="100vh"
      as={motion.div}
      layout
      overflow="hidden"
      position="relative"
    >
    <div className="grain-overlay" aria-hidden="true" />
      <Box
        position="fixed"
        inset="0"
        bg=""
        zIndex={-1}
      >

        {/* (41, 37, 37, 0.9) */}
        {/* <StarRainBackground /> */}
        {/* <Noise patternAlpha={20} blendMode="overlay"/> */}
        
      </Box>
      {/* main container which will hold everything */}
      <MotionVStack
        spacing={10}
        p={8}
        as="header"
        layout
        align="center"
        textAlign="center"
        animate={{ scale: isChatOpen ? 0.95 : 1 }}
        transition={{ duration: 0.4 }}
      >
        <Header />

        <AnimatePresence>
          {!isChatOpen ? (
            <MotionBox
              key="welcome-input"
              w="100%"
              maxW="2xl"
              // initial={{ opacity: 0, y: 100 }}
              // animate={{ opacity: 1, y: 0 }}
              // exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.4, ease: "easeInOut" }}
              layout
            >
              <WelcomeInput onStartChat={handleStartChat} />
              <FeaturesFloating />
            </MotionBox>
          ) : (
            <MotionBox
              key="chat-box"
              w="100%"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              // exit={{ opacity: 0, scale: 0 }}
              transition={{ duration: 0.4, ease: "easeInOut" }}
              layout
            >
              <ChatBox 
              messages={messages}
              setMessages={setMessages}
              sessionId = {sessionID}
              initialMessage={initialMessage}
              
              />
            </MotionBox>
          )}
        </AnimatePresence>
      </MotionVStack>

      <Footer />
    </Box>
  );
}

export default App;
