/*
Minetest
Copyright (C) 2010-2013 celeron55, Perttu Ahola <celeron55@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*/

#pragma once

#include "irrlichttypes_extrabloated.h"
#include "client/inputhandler.h"
#include <zmqpp/zmqpp.hpp>
#include <string>

class DumbClientInputHandler : public InputHandler
{
public:
	DumbClientInputHandler(std::string zmq_port): client(context, zmqpp::socket_type::reply) {
		try {
        	client.bind(zmq_port);
		} catch (zmqpp::zmq_internal_exception &e) {
			errorstream << "ZeroMQ error: " << e.what() << " (port: " << zmq_port << ")" << std::endl;
			throw e;
		};
    };

	virtual bool isKeyDown(GameKeyType k) { return keydown[keycache.key[k]]; }
	virtual bool wasKeyDown(GameKeyType k) { return false; }
	virtual bool wasKeyPressed(GameKeyType k) { return false; }
	virtual bool wasKeyReleased(GameKeyType k) { return false; }
	virtual bool cancelPressed() { return false; }
	virtual float getMovementSpeed() { return movementSpeed; }
	virtual float getMovementDirection() { return movementDirection; }
	virtual v2s32 getMousePos() { return mousepos; }
	virtual void setMousePos(s32 x, s32 y) { mousepos = v2s32(x, y); }

	virtual s32 getMouseWheel() { return 0; }

	virtual void step(float dtime) {
		// TODO
	};

	s32 Rand(s32 min, s32 max);

private:
    zmqpp::context context;
    zmqpp::socket client;
	KeyList keydown;
	v2s32 mousepos;
	v2s32 mousespeed;
	float movementSpeed;
	float movementDirection;
};